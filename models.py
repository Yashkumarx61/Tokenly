from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Business(UserMixin, db.Model):
    __tablename__ = 'businesses'
    
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(120), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(60), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    theme_preference = db.Column(db.String(20), default='crimson')
    address = db.Column(db.String(255), default='Main Terminal Counter')
    gstin = db.Column(db.String(25), nullable=True)
    
    subscription_active = db.Column(db.Boolean, default=True)
    subscription_start = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_expires = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=365))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    categories = db.relationship('Category', backref='business', lazy=True, cascade='all, delete-orphan')
    items = db.relationship('MenuItem', backref='business', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='business', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_subscription_valid(self):
        if not self.subscription_active:
            return False
        if self.subscription_expires:
            return datetime.utcnow() <= self.subscription_expires
        return True

    @property
    def days_remaining(self):
        if not self.subscription_expires:
            return 365
        delta = self.subscription_expires - datetime.utcnow()
        return max(0, delta.days)


class OTPRecord(db.Model):
    __tablename__ = 'otp_records'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    otp_code = db.Column(db.String(10), nullable=False)
    verification_token = db.Column(db.String(100), nullable=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    attempt_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False, index=True)
    name = db.Column(db.String(60), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    
    items = db.relationship('MenuItem', backref='category', lazy=True, cascade='all, delete-orphan')


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    half_price = db.Column(db.Float, nullable=True)
    full_price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    is_veg = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DailyTokenSequence(db.Model):
    __tablename__ = 'daily_token_sequences'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False, index=True)
    date_key = db.Column(db.String(10), nullable=False, index=True)
    last_token_num = db.Column(db.Integer, default=0, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('business_id', 'date_key', name='_business_date_token_uc'),
    )


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False, index=True)
    token_number = db.Column(db.String(20), nullable=False)
    raw_token_num = db.Column(db.Integer, nullable=False)
    date_key = db.Column(db.String(10), nullable=False, index=True)
    
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_amount = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, nullable=False, default=0.0)
    grand_total = db.Column(db.Float, nullable=False, default=0.0)
    
    payment_method = db.Column(db.String(20), default='cash')
    status = db.Column(db.String(20), default='completed')
    customer_name = db.Column(db.String(100), nullable=True)
    table_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=True)
    
    item_name = db.Column(db.String(100), nullable=False)
    portion = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
