from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, MenuItem, Category, Business
from forms import MenuItemForm, CategoryForm
from utils import save_uploaded_image, log_audit_event

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def dashboard():
    categories = Category.query.filter_by(business_id=current_user.id).order_by(Category.sort_order.asc(), Category.name.asc()).all()
    items = MenuItem.query.filter_by(business_id=current_user.id).all()
    
    item_form = MenuItemForm()
    item_form.category_id.choices = [(c.id, c.name) for c in categories]
    cat_form = CategoryForm()
    
    return render_template(
        'admin/dashboard.html',
        categories=categories,
        items=items,
        item_form=item_form,
        cat_form=cat_form,
        business=current_user
    )

@admin_bp.route('/items/add', methods=['POST'])
@login_required
def add_item():
    categories = Category.query.filter_by(business_id=current_user.id).all()
    form = MenuItemForm()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    # Handle optional image file upload
    image_url = None
    if 'image_file' in request.files:
        uploaded_path = save_uploaded_image(request.files['image_file'])
        if uploaded_path:
            image_url = uploaded_path

    if not image_url and form.image_url.data:
        image_url = form.image_url.data.strip()

    if form.validate_on_submit():
        cat = Category.query.filter_by(id=form.category_id.data, business_id=current_user.id).first()
        if not cat:
            flash('Invalid category selected.', 'danger')
            return redirect(url_for('admin.dashboard'))

        item = MenuItem(
            business_id=current_user.id,
            category_id=form.category_id.data,
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            half_price=form.half_price.data if form.half_price.data else None,
            full_price=form.full_price.data,
            image_url=image_url,
            is_veg=form.is_veg.data,
            is_available=form.is_available.data
        )
        db.session.add(item)
        db.session.commit()
        
        log_audit_event(current_user.id, 'ADD_MENU_ITEM', f"Added menu item '{item.name}'")
        flash(f"Menu item '{item.name}' added successfully!", 'success')
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"Error in {field}: {err}", 'danger')
                
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/items/edit/<int:item_id>', methods=['POST'])
@login_required
def edit_item(item_id):
    item = MenuItem.query.filter_by(id=item_id, business_id=current_user.id).first_or_404()
    
    name = request.form.get('name', '').strip()
    category_id = int(request.form.get('category_id', 0))
    description = request.form.get('description', '').strip()
    half_price_raw = request.form.get('half_price', '').strip()
    full_price_raw = request.form.get('full_price', '').strip()
    image_url_raw = request.form.get('image_url', '').strip()
    is_veg = 'is_veg' in request.form
    is_available = 'is_available' in request.form
    
    if not name or not full_price_raw or not category_id:
        flash('Please fill in required fields (Name, Category, Full Price).', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Handle image file upload if provided
    image_url = item.image_url
    if 'image_file' in request.files and request.files['image_file'].filename != '':
        uploaded_path = save_uploaded_image(request.files['image_file'])
        if uploaded_path:
            image_url = uploaded_path
    elif image_url_raw:
        image_url = image_url_raw

    item.name = name
    item.category_id = category_id
    item.description = description if description else None
    item.half_price = float(half_price_raw) if half_price_raw else None
    item.full_price = float(full_price_raw)
    item.image_url = image_url
    item.is_veg = is_veg
    item.is_available = is_available
    
    db.session.commit()
    log_audit_event(current_user.id, 'EDIT_MENU_ITEM', f"Updated item '{item.name}' (Full: ₹{item.full_price})")
    flash(f"Item '{item.name}' updated successfully!", 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/items/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = MenuItem.query.filter_by(id=item_id, business_id=current_user.id).first_or_404()
    item_name = item.name
    db.session.delete(item)
    db.session.commit()
    log_audit_event(current_user.id, 'DELETE_MENU_ITEM', f"Deleted item '{item_name}'")
    flash(f"Item '{item_name}' deleted.", 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/items/toggle/<int:item_id>', methods=['POST'])
@login_required
def toggle_item(item_id):
    item = MenuItem.query.filter_by(id=item_id, business_id=current_user.id).first_or_404()
    item.is_available = not item.is_available
    db.session.commit()
    status_str = "Available" if item.is_available else "Out of Stock"
    return jsonify({'success': True, 'is_available': item.is_available, 'status_str': status_str})

@admin_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(
            business_id=current_user.id,
            name=form.name.data.strip(),
            sort_order=form.sort_order.data or 1
        )
        db.session.add(cat)
        db.session.commit()
        log_audit_event(current_user.id, 'ADD_CATEGORY', f"Added category '{cat.name}'")
        flash(f"Category '{cat.name}' created successfully!", 'success')
    else:
        flash('Failed to create category. Please check name input.', 'danger')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/categories/delete/<int:cat_id>', methods=['POST'])
@login_required
def delete_category(cat_id):
    cat = Category.query.filter_by(id=cat_id, business_id=current_user.id).first_or_404()
    cat_name = cat.name
    db.session.delete(cat)
    db.session.commit()
    log_audit_event(current_user.id, 'DELETE_CATEGORY', f"Deleted category '{cat_name}'")
    flash(f"Category '{cat_name}' and its items removed.", 'info')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/theme', methods=['POST'])
@login_required
def set_theme():
    theme = request.form.get('theme') or request.json.get('theme') if request.is_json else 'crimson'
    if theme in ['crimson', 'blue']:
        current_user.theme_preference = theme
        db.session.commit()
        return jsonify({'success': True, 'theme': theme})
    return jsonify({'success': False, 'error': 'Invalid theme option'}), 400
