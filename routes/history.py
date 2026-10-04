from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func
from models import db, Order, OrderItem
from utils import calculate_item_price

history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/')
@login_required
def order_logs():
    preset = request.args.get('preset', 'today')
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()
    search_query = request.args.get('search', '').strip()

    today_dt = datetime.utcnow().date()

    if preset == 'today':
        start_date = today_dt
        end_date = today_dt
    elif preset == 'yesterday':
        start_date = today_dt - timedelta(days=1)
        end_date = start_date
    elif preset == 'week':
        start_date = today_dt - timedelta(days=7)
        end_date = today_dt
    elif preset == 'month':
        start_date = today_dt - timedelta(days=30)
        end_date = today_dt
    elif preset == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today_dt
            end_date = today_dt
            flash('Invalid custom date format. Defaulting to Today.', 'warning')
    else:
        # All time or fallback
        start_date = None
        end_date = None

    # Strict multi-tenant query building
    query = Order.query.filter_by(business_id=current_user.id)

    if start_date and end_date:
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Order.created_at >= start_dt, Order.created_at <= end_dt)

    if search_query:
        search_fmt = f"%{search_query}%"
        query = query.filter(
            (Order.token_number.ilike(search_fmt)) |
            (Order.customer_name.ilike(search_fmt)) |
            (Order.table_number.ilike(search_fmt)) |
            (Order.payment_method.ilike(search_fmt))
        )

    orders = query.order_by(Order.created_at.desc()).all()

    # Calculate Summary Metrics
    total_orders = len(orders)
    total_revenue = sum(o.grand_total for o in orders)
    avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0.0

    cash_total = sum(o.grand_total for o in orders if o.payment_method == 'cash')
    upi_total = sum(o.grand_total for o in orders if o.payment_method == 'upi')
    card_total = sum(o.grand_total for o in orders if o.payment_method == 'card')

    return render_template(
        'history/orders.html',
        orders=orders,
        preset=preset,
        start_date=start_date.strftime('%Y-%m-%d') if start_date else '',
        end_date=end_date.strftime('%Y-%m-%d') if end_date else '',
        search_query=search_query,
        total_orders=total_orders,
        total_revenue=f"{total_revenue:.2f}",
        avg_order_value=f"{avg_order_value:.2f}",
        cash_total=f"{cash_total:.2f}",
        upi_total=f"{upi_total:.2f}",
        card_total=f"{card_total:.2f}",
        business=current_user
    )

@history_bp.route('/reprint/<int:order_id>')
@login_required
def reprint_receipt(order_id):
    order = Order.query.filter_by(id=order_id, business_id=current_user.id).first_or_404()
    
    items_list = []
    for item in order.items:
        items_list.append({
            'name': item.item_name,
            'portion': item.portion,
            'quantity': item.quantity,
            'unit_price': f"₹{item.unit_price:.2f}",
            'total_price': f"₹{item.total_price:.2f}"
        })

    receipt_data = {
        'order_id': order.id,
        'token_number': order.token_number,
        'business_name': current_user.business_name,
        'address': current_user.address or '',
        'phone': current_user.phone or '',
        'gstin': current_user.gstin or '',
        'date_time': order.created_at.strftime('%d-%b-%Y %I:%M %p'),
        'payment_method': (order.payment_method or 'CASH').upper(),
        'customer_name': order.customer_name or '',
        'table_number': order.table_number or '',
        'items': items_list,
        'subtotal': f"₹{order.subtotal:.2f}",
        'discount': f"₹{order.discount_amount:.2f}",
        'tax': f"₹{order.tax_amount:.2f}",
        'grand_total': f"₹{order.grand_total:.2f}"
    }

    return jsonify({'success': True, 'receipt': receipt_data})
