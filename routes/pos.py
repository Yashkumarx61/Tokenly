from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from models import db, MenuItem, Category, Order, OrderItem
from utils import generate_daily_token, calculate_item_price, log_audit_event

pos_bp = Blueprint('pos', __name__)

@pos_bp.route('/pos')
@login_required
def terminal():
    if not current_user.is_subscription_valid:
        flash('Your annual subscription has expired. Please renew to access the POS terminal.', 'warning')
        return redirect(url_for('auth.subscription'))

    categories = Category.query.filter_by(business_id=current_user.id).order_by(Category.sort_order.asc(), Category.name.asc()).all()
    items = MenuItem.query.filter_by(business_id=current_user.id, is_available=True).all()
    
    return render_template(
        'pos/terminal.html',
        categories=categories,
        items=items,
        business=current_user
    )

@pos_bp.route('/api/pos/checkout', methods=['POST'])
@login_required
def checkout():
    if not current_user.is_subscription_valid:
        return jsonify({'success': False, 'error': 'Subscription expired. Please renew.'}), 403

    data = request.get_json() or {}
    cart_items = data.get('items', [])
    payment_method = data.get('payment_method', 'cash')
    discount_input = float(data.get('discount', 0.0) or 0.0)

    if not cart_items:
        return jsonify({'success': False, 'error': 'Cart is empty. Please add items before checking out.'}), 400

    # Server-Side Financial Calculation & Data Isolation
    calculated_subtotal = 0.0
    order_items_to_create = []

    for entry in cart_items:
        item_id = int(entry.get('item_id'))
        portion = str(entry.get('portion', 'full')).lower()
        quantity = int(entry.get('quantity', 1))

        if quantity <= 0:
            continue

        # Strict Multi-Tenant DB Query
        menu_item = MenuItem.query.filter_by(id=item_id, business_id=current_user.id).first()
        if not menu_item:
            return jsonify({'success': False, 'error': f'Item ID {item_id} not found in your menu.'}), 404

        if portion == 'half':
            if menu_item.half_price is None or menu_item.half_price <= 0:
                return jsonify({'success': False, 'error': f'{menu_item.name} does not have Half portion pricing.'}), 400
            unit_price = calculate_item_price(menu_item.half_price)
        else:
            portion = 'full'
            unit_price = calculate_item_price(menu_item.full_price)

        line_total = calculate_item_price(unit_price * quantity)
        calculated_subtotal += line_total

        order_items_to_create.append({
            'menu_item': menu_item,
            'item_name': menu_item.name,
            'portion': portion,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': line_total
        })

    if not order_items_to_create:
        return jsonify({'success': False, 'error': 'No valid items in cart.'}), 400

    # Server side discount & totals
    calculated_subtotal = calculate_item_price(calculated_subtotal)
    discount_amount = calculate_item_price(min(discount_input, calculated_subtotal))
    taxable_amount = calculate_item_price(calculated_subtotal - discount_amount)
    tax_amount = 0.0
    grand_total = calculate_item_price(taxable_amount + tax_amount)

    try:
        # Atomic Transaction locked Sequential Daily Token generation (#001, #002)
        raw_num, token_str = generate_daily_token(current_user.id)
        today_date_key = datetime.utcnow().strftime('%Y-%m-%d')

        new_order = Order(
            business_id=current_user.id,
            token_number=token_str,
            raw_token_num=raw_num,
            date_key=today_date_key,
            subtotal=calculated_subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            grand_total=grand_total,
            payment_method=payment_method,
            status='completed',
            created_at=datetime.utcnow()
        )
        db.session.add(new_order)
        db.session.flush()

        items_summary_list = []
        for item_data in order_items_to_create:
            oi = OrderItem(
                business_id=current_user.id,
                order_id=new_order.id,
                item_id=item_data['menu_item'].id,
                item_name=item_data['item_name'],
                portion=item_data['portion'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            db.session.add(oi)
            items_summary_list.append({
                'name': item_data['item_name'],
                'portion': item_data['portion'],
                'quantity': item_data['quantity'],
                'unit_price': f"₹{item_data['unit_price']:.2f}",
                'total_price': f"₹{item_data['total_price']:.2f}"
            })

        db.session.commit()

        log_audit_event(
            current_user.id, 
            'NEW_ORDER_GENERATED', 
            f"Token {token_str} generated. Total: ₹{grand_total:.2f}, Payment: {payment_method.upper()}"
        )

        receipt_data = {
            'order_id': new_order.id,
            'token_number': token_str,
            'business_name': current_user.business_name,
            'address': current_user.address or '',
            'phone': current_user.phone or '',
            'date_time': new_order.created_at.strftime('%d-%b-%Y %I:%M %p'),
            'payment_method': payment_method.upper(),
            'items': items_summary_list,
            'subtotal': f"₹{calculated_subtotal:.2f}",
            'discount': f"₹{discount_amount:.2f}",
            'tax': f"₹{tax_amount:.2f}",
            'grand_total': f"₹{grand_total:.2f}"
        }

        return jsonify({
            'success': True,
            'message': 'Token generated successfully!',
            'token_number': token_str,
            'receipt': receipt_data
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to process order: {str(e)}'}), 500
