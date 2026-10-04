import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tokenly-super-secret-key-2026-production-secure')
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'tokenly.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Target UPI VPA Payment Parameters
    UPI_VPA = os.environ.get('UPI_VPA', '9053088708@ptyes')
    UPI_PAYEE_NAME = os.environ.get('UPI_PAYEE_NAME', 'TOKENLY')
    UPI_TRANSACTION_NOTE = 'TOKENLY Annual POS Access'
    
    # Updated Annual Plan Subscription Price (₹1,999 / year)
    ANNUAL_SUBSCRIPTION_PRICE = 1999
    SUBSCRIPTION_DURATION_DAYS = 365
    
    # OTP Settings
    OTP_EXPIRY_MINUTES = 5
    OTP_MAX_ATTEMPTS = 3
    OTP_COOLDOWN_SECONDS = 60
    
    # Rate Limiting Settings
    RATELIMIT_DEFAULT = "200 per day; 50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"
    
    # Live SMS Gateway API Keys & Credentials
    FAST2SMS_API_KEY = os.environ.get('FAST2SMS_API_KEY', '')
    TWO_FACTOR_API_KEY = os.environ.get('TWO_FACTOR_API_KEY', '')
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
    MSG91_API_KEY = os.environ.get('MSG91_API_KEY', '')
    MSG91_TEMPLATE_ID = os.environ.get('MSG91_TEMPLATE_ID', '')
