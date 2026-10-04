"""
Tokenly Core Utility Functions
Provides strict input validation, precise financial math, secure file uploads,
and atomic transaction-locked token generation.
"""

import os
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Optional, Any
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from models import db, DailyTokenSequence, Category, MenuItem, AuditLog

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'uploads'))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename: str) -> bool:
    """
    Checks if an uploaded file has a safe image extension.
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def save_uploaded_image(file_storage: Optional[FileStorage]) -> Optional[str]:
    """
    Validates and saves an uploaded image file securely to static/uploads/.
    Returns relative URL string or None if file is missing/invalid.
    """
    if not file_storage or not file_storage.filename or file_storage.filename.strip() == '':
        return None
        
    filename = secure_filename(file_storage.filename)
    if allowed_file(filename):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}_{int(datetime.utcnow().timestamp())}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file_storage.save(filepath)
        return f"/static/uploads/{unique_filename}"
    return None

def get_today_date_key() -> str:
    """Returns today's date formatted as YYYY-MM-DD."""
    return datetime.utcnow().strftime('%Y-%m-%d')

def generate_daily_token(business_id: int) -> Tuple[int, str]:
    """
    Generates a sequential daily token number (e.g., #001, #002) for a given business_id.
    Uses database row-level locking (with_for_update) to prevent race conditions during peak rushes.
    """
    if not isinstance(business_id, int) or business_id <= 0:
        raise ValueError("Invalid business_id provided for token generation.")

    date_key = get_today_date_key()
    
    seq = DailyTokenSequence.query.filter_by(
        business_id=business_id, 
        date_key=date_key
    ).with_for_update().first()
    
    if not seq:
        seq = DailyTokenSequence(
            business_id=business_id,
            date_key=date_key,
            last_token_num=1
        )
        db.session.add(seq)
    else:
        seq.last_token_num += 1
        
    db.session.commit()
    
    raw_num = seq.last_token_num
    token_str = f"#{raw_num:03d}"
    return raw_num, token_str

def calculate_item_price(price_val: Any) -> float:
    """
    Ensures zero financial rounding errors by quantizing price inputs to 2 decimal places.
    Handles None, strings, floats, and integers safely.
    """
    if price_val is None:
        return 0.0
    try:
        d = Decimal(str(price_val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return max(0.0, float(d))
    except (ValueError, TypeError, ArithmeticError):
        return 0.0

def log_audit_event(business_id: int, action: str, details: Optional[str] = None) -> None:
    """
    Logs immutable audit events for financial transactions and menu changes.
    """
    if not business_id or not action:
        return
    try:
        log = AuditLog(business_id=business_id, action=action, details=details)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

def seed_default_menu(business_id: int) -> None:
    """
    Populates initial default categories and menu items for a newly registered business.
    """
    if not isinstance(business_id, int) or business_id <= 0:
        return

    cat_chinese = Category(business_id=business_id, name="Chinese", sort_order=1)
    cat_noodles = Category(business_id=business_id, name="Noodles", sort_order=2)
    cat_rolls = Category(business_id=business_id, name="Rolls & Momos", sort_order=3)
    cat_burgers = Category(business_id=business_id, name="Burgers & Snacks", sort_order=4)
    cat_beverages = Category(business_id=business_id, name="Beverages", sort_order=5)
    
    db.session.add_all([cat_chinese, cat_noodles, cat_rolls, cat_burgers, cat_beverages])
    db.session.commit()
    
    chinese_items = [
        MenuItem(
            business_id=business_id,
            category_id=cat_chinese.id,
            name="Manchurian Dry",
            description="Crispy vegetable balls tossed in soya garlic sauce",
            half_price=70.0,
            full_price=130.0,
            image_url="https://images.unsplash.com/photo-1512058564366-18510be2db19?w=500&auto=format&fit=crop&q=60",
            is_veg=True
        ),
        MenuItem(
            business_id=business_id,
            category_id=cat_chinese.id,
            name="Manchurian Gravy",
            description="Classic Manchurian balls in rich savory gravy",
            half_price=80.0,
            full_price=140.0,
            image_url="https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=500&auto=format&fit=crop&q=60",
            is_veg=True
        ),
        MenuItem(
            business_id=business_id,
            category_id=cat_chinese.id,
            name="Chilli Potato",
            description="Crispy fried potato strips in sweet & spicy chilli glaze",
            half_price=70.0,
            full_price=130.0,
            image_url="https://images.unsplash.com/photo-1585032226651-759b368d7246?w=500&auto=format&fit=crop&q=60",
            is_veg=True
        )
    ]
    
    noodles_items = [
        MenuItem(
            business_id=business_id,
            category_id=cat_noodles.id,
            name="Hakha Chowmein",
            description="Stir-fried noodles with fresh vegetables & schezwan seasoning",
            half_price=60.0,
            full_price=110.0,
            image_url="https://images.unsplash.com/photo-1612927601601-6638404737ce?w=500&auto=format&fit=crop&q=60",
            is_veg=True
        )
    ]
    
    rolls_items = [
        MenuItem(
            business_id=business_id,
            category_id=cat_rolls.id,
            name="Spring Roll",
            description="Golden fried roll filled with shredded veggies & noodles",
            half_price=40.0,
            full_price=70.0,
            image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=500&auto=format&fit=crop&q=60",
            is_veg=True
        )
    ]
    
    db.session.add_all(chinese_items + noodles_items + rolls_items)
    db.session.commit()
