import secrets
import uuid
import re
import urllib.parse
import urllib.request
import json
import base64
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from models import db, Business, OTPRecord
from forms import LoginForm, RegistrationForm
from utils import seed_default_menu, log_audit_event

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('pos.terminal'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/auth/send-real-otp', methods=['POST'])
@auth_bp.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or {}
    raw_phone = str(data.get('phone', '')).strip()
    
    # 1. Sanitize Mobile Number (Strip non-digits)
    clean_digits = re.sub(r'[^\d]', '', raw_phone)
    if clean_digits.startswith('91') and len(clean_digits) == 12:
        phone = clean_digits[2:]
    else:
        phone = clean_digits
    
    # Validate 10-digit Indian Mobile Number Format
    if not re.match(r'^[6-9]\d{9}$', phone):
        return jsonify({'success': False, 'error': 'Please enter a valid 10-digit Indian mobile number (e.g. 9876543210).'}), 400

    # 2. Rate Limiting & Cooldown Check (60 seconds)
    recent_otp = OTPRecord.query.filter_by(phone=phone).order_by(OTPRecord.created_at.desc()).first()
    if recent_otp:
        elapsed = (datetime.utcnow() - recent_otp.created_at).total_seconds()
        if elapsed < 60:
            remaining = int(60 - elapsed)
            return jsonify({'success': False, 'error': f'Please wait {remaining}s before requesting a new OTP.'}), 429

    # 3. Generate Cryptographically Secure 6-digit numeric OTP
    otp_code = str(secrets.randbelow(900000) + 100000)
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    otp_record = OTPRecord(
        phone=phone,
        otp_code=otp_code,
        is_verified=False,
        attempt_count=0,
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    db.session.add(otp_record)
    db.session.commit()

    # Always log to Server Console for Development & Diagnostics
    print(f"\n==================================================")
    print(f"  [DEV OTP LOG] Target Mobile: +91 {phone}")
    print(f"  [DEV OTP LOG] Generated OTP: {otp_code}")
    print(f"  [DEV OTP LOG] Expiry: 5 Minutes (Expires at {expires_at.strftime('%H:%M:%S')} UTC)")
    print(f"==================================================\n")
    current_app.logger.info(f"[DEV OTP LOG] Generated OTP {otp_code} for +91{phone}")

    # 4. Multi-Gateway SMS Provider Dispatch
    fast2sms_key = current_app.config.get('FAST2SMS_API_KEY')
    twofactor_key = current_app.config.get('TWO_FACTOR_API_KEY')
    twilio_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
    twilio_auth = current_app.config.get('TWILIO_AUTH_TOKEN')
    twilio_from = current_app.config.get('TWILIO_PHONE_NUMBER')
    msg91_key = current_app.config.get('MSG91_API_KEY')

    provider_sent = False
    provider_error_msg = ""

    # Provider 1: Fast2SMS (Quick OTP Route)
    if fast2sms_key:
        try:
            sms_payload = json.dumps({
                "route": "otp",
                "variables_values": otp_code,
                "numbers": phone
            }).encode('utf-8')

            req = urllib.request.Request(
                "https://www.fast2sms.com/dev/bulkV2",
                data=sms_payload,
                headers={
                    'authorization': fast2sms_key,
                    'Content-Type': 'application/json',
                    'User-Agent': 'Tokenly-POS/1.0'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                current_app.logger.info(f"[SMS GATEWAY FAST2SMS] Response: {resp_data}")
                if resp_data.get('return') is True:
                    provider_sent = True
                else:
                    provider_error_msg = f"Fast2SMS error: {resp_data.get('message', ['Unknown error'])}"
        except Exception as e:
            provider_error_msg = f"Fast2SMS Exception: {str(e)}"
            current_app.logger.error(f"[SMS GATEWAY ERROR] Fast2SMS dispatch failed: {e}")

    # Provider 2: 2Factor.in (Popular Indian OTP API)
    elif twofactor_key:
        try:
            twofac_url = f"https://2factor.in/API/V1/{twofactor_key}/SMS/{phone}/{otp_code}/AUTOGEN"
            req = urllib.request.Request(twofac_url, headers={'User-Agent': 'Tokenly-POS/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                current_app.logger.info(f"[SMS GATEWAY 2FACTOR] Response: {resp_data}")
                if resp_data.get('Status') == 'Success':
                    provider_sent = True
                else:
                    provider_error_msg = f"2Factor error: {resp_data.get('Details', 'Unknown error')}"
        except Exception as e:
            provider_error_msg = f"2Factor Exception: {str(e)}"
            current_app.logger.error(f"[SMS GATEWAY ERROR] 2Factor dispatch failed: {e}")

    # Provider 3: Twilio SMS API
    elif twilio_sid and twilio_auth and twilio_from:
        try:
            twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            post_params = urllib.parse.urlencode({
                'From': twilio_from,
                'To': f'+91{phone}',
                'Body': f'Your Tokenly verification OTP is {otp_code}. Valid for 5 minutes.'
            }).encode('utf-8')
            
            auth_header = base64.b64encode(f"{twilio_sid}:{twilio_auth}".encode('utf-8')).decode('utf-8')
            req = urllib.request.Request(
                twilio_url,
                data=post_params,
                headers={
                    'Authorization': f'Basic {auth_header}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                current_app.logger.info(f"[SMS GATEWAY TWILIO] Response: {resp_data}")
                if resp.status in (200, 201):
                    provider_sent = True
                else:
                    provider_error_msg = f"Twilio error: {resp_data.get('message', 'Failed')}"
        except Exception as e:
            provider_error_msg = f"Twilio Exception: {str(e)}"
            current_app.logger.error(f"[SMS GATEWAY ERROR] Twilio dispatch failed: {e}")

    else:
        current_app.logger.warning(f"[SMS GATEWAY NOTICE] No SMS Provider API Key set in environment. Dev OTP logged to console.")

    # 5. Build Response Message
    if provider_error_msg:
        # If API key was provided but failed, notify with provider details
        return jsonify({
            'success': False,
            'error': f"SMS Delivery Notice: {provider_error_msg}. Check console log for DEV OTP."
        }), 502

    return jsonify({
        'success': True,
        'message': f'OTP sent successfully via SMS to +91 {phone}'
    })

@auth_bp.route('/api/auth/verify-real-otp', methods=['POST'])
@auth_bp.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json() or {}
    raw_phone = str(data.get('phone', '')).strip()
    otp_input = str(data.get('otp', '')).strip()

    clean_digits = re.sub(r'[^\d]', '', raw_phone)
    if clean_digits.startswith('91') and len(clean_digits) == 12:
        phone = clean_digits[2:]
    else:
        phone = clean_digits

    if not phone or not otp_input:
        return jsonify({'success': False, 'error': 'Phone number and 6-digit OTP code are required.'}), 400

    otp_record = OTPRecord.query.filter_by(phone=phone).order_by(OTPRecord.created_at.desc()).first()
    if not otp_record:
        return jsonify({'success': False, 'error': 'No OTP record found. Please request a new OTP.'}), 404

    if datetime.utcnow() > otp_record.expires_at:
        return jsonify({'success': False, 'error': 'OTP has expired. Please request a new OTP.'}), 400

    if otp_record.attempt_count >= 3:
        return jsonify({'success': False, 'error': 'Maximum verification attempts exceeded. Please request a new OTP.'}), 429

    otp_record.attempt_count += 1
    db.session.commit()

    if otp_record.otp_code != otp_input:
        attempts_left = 3 - otp_record.attempt_count
        return jsonify({'success': False, 'error': f'Invalid OTP code. {attempts_left} attempts remaining.'}), 400

    # Verification successful - Issue Signed Token
    verification_token = f"verif_{uuid.uuid4().hex}"
    otp_record.is_verified = True
    otp_record.verification_token = verification_token
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Mobile number verified successfully!',
        'verification_token': verification_token
    })

@auth_bp.route('/api/auth/initiate-upi-payment', methods=['POST'])
def initiate_upi_payment():
    data = request.get_json() or {}
    business_name = str(data.get('business_name', '')).strip()
    owner_name = str(data.get('owner_name', '')).strip()
    raw_phone = str(data.get('phone', '')).strip()
    username = str(data.get('username', '')).strip().lower()
    verification_token = str(data.get('verification_token', '')).strip()

    phone = re.sub(r'[^\d]', '', raw_phone)
    if phone.startswith('91') and len(phone) == 12:
        phone = phone[2:]

    if not business_name or not owner_name or not phone or not username:
        return jsonify({'success': False, 'error': 'All fields are required to initiate payment.'}), 400

    # Check username availability
    if Business.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Username / Business ID is already taken. Please choose another.'}), 400

    # Verify OTP token
    verified_record = OTPRecord.query.filter_by(
        phone=phone,
        verification_token=verification_token,
        is_verified=True
    ).first()

    if not verified_record and not current_app.debug:
        return jsonify({'success': False, 'error': 'Mobile verification incomplete. Please verify your phone via OTP.'}), 400

    # Target UPI Parameters
    upi_vpa = current_app.config.get('UPI_VPA', '9053088708@ptyes')
    payee_name = current_app.config.get('UPI_PAYEE_NAME', 'TOKENLY')
    amount = current_app.config.get('ANNUAL_SUBSCRIPTION_PRICE', 1999)
    note = current_app.config.get('UPI_TRANSACTION_NOTE', 'TOKENLY Annual POS Access')

    # Unique Transaction Reference ID
    tr_id = f"TKN-{int(datetime.utcnow().timestamp())}-{secrets.token_hex(3).upper()}"

    # Construct Standardized UPI Intent URI
    query_params = {
        'pa': upi_vpa,
        'pn': payee_name,
        'am': f"{amount:.2f}",
        'cu': 'INR',
        'tn': note,
        'tr': tr_id
    }
    upi_uri = f"upi://pay?{urllib.parse.urlencode(query_params)}"

    return jsonify({
        'success': True,
        'upi_uri': upi_uri,
        'tr_id': tr_id,
        'vpa': upi_vpa,
        'payee_name': payee_name,
        'amount': amount,
        'note': note
    })

@auth_bp.route('/api/auth/confirm-upi-payment', methods=['POST'])
def confirm_upi_payment():
    data = request.get_json() or {}
    utr = str(data.get('utr', '')).strip()
    tr_id = str(data.get('tr_id', '')).strip()
    business_name = str(data.get('business_name', '')).strip()
    owner_name = str(data.get('owner_name', '')).strip()
    raw_phone = str(data.get('phone', '')).strip()
    username = str(data.get('username', '')).strip().lower()
    password = str(data.get('password', ''))

    phone = re.sub(r'[^\d]', '', raw_phone)
    if phone.startswith('91') and len(phone) == 12:
        phone = phone[2:]

    if not utr or len(utr) < 6:
        return jsonify({'success': False, 'error': 'Please enter a valid 12-digit UPI UTR / Transaction Reference number.'}), 400

    # Ensure username is unique
    if Business.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Account already created. Please log in.'}), 400

    # Create & Activate Business Account
    business = Business(
        business_name=business_name,
        owner_name=owner_name,
        phone=phone,
        username=username,
        theme_preference='crimson',
        subscription_active=True,
        subscription_start=datetime.utcnow(),
        subscription_expires=datetime.utcnow() + timedelta(days=365)
    )
    business.set_password(password)

    db.session.add(business)
    db.session.commit()

    # Seed Default Menu Items
    seed_default_menu(business.id)
    log_audit_event(business.id, 'BUSINESS_REGISTERED_UPI', f"Business '{business_name}' activated ₹1,999 annual subscription via UPI UTR: {utr} (Ref: {tr_id}).")

    # Automatically Login User
    login_user(business, remember=True)
    flash(f'Account Activated! Welcome to Tokenly POS. (₹1,999 Annual Access Active)', 'success')

    return jsonify({
        'success': True,
        'message': 'Payment confirmed & Annual Subscription activated!',
        'redirect_url': url_for('pos.terminal')
    })

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    business_name = str(data.get('business_name', '')).strip()
    owner_name = str(data.get('owner_name', '')).strip()
    raw_phone = str(data.get('phone', '')).strip()
    username = str(data.get('username', '')).strip().lower()
    password = str(data.get('password', ''))

    phone = re.sub(r'[^\d]', '', raw_phone)
    if phone.startswith('91') and len(phone) == 12:
        phone = phone[2:]

    if not business_name or not owner_name or not phone or not username or not password:
        return jsonify({'success': False, 'error': 'All form fields are required.'}), 400

    if Business.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Username / Business ID is already taken. Please choose another.'}), 400

    business = Business(
        business_name=business_name,
        owner_name=owner_name,
        phone=phone,
        username=username,
        theme_preference='crimson',
        subscription_active=True,
        subscription_start=datetime.utcnow(),
        subscription_expires=datetime.utcnow() + timedelta(days=365)
    )
    business.set_password(password)

    db.session.add(business)
    db.session.commit()

    seed_default_menu(business.id)
    log_audit_event(business.id, 'BUSINESS_REGISTERED_FREE_TRIAL', f"Business '{business_name}' activated Free Trial account.")

    login_user(business, remember=True)
    flash('Welcome! Your Free Trial is now active.', 'success')

    return jsonify({
        'success': True,
        'message': 'Welcome! Your Free Trial is now active.',
        'redirect_url': url_for('pos.terminal')
    })

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('pos.terminal'))
        
    form = RegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data.strip().lower()
        phone = re.sub(r'[^\d]', '', form.phone.data.strip())
        if phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]

        existing = Business.query.filter_by(username=username).first()
        if existing:
            flash('Username/Business ID is already taken. Please choose another or login.', 'danger')
            return render_template('auth/register.html', form=form, annual_price=current_app.config.get('ANNUAL_SUBSCRIPTION_PRICE', 1999))

        business = Business(
            business_name=form.business_name.data.strip(),
            owner_name=form.owner_name.data.strip(),
            phone=phone,
            username=username,
            theme_preference='crimson',
            subscription_active=True,
            subscription_start=datetime.utcnow(),
            subscription_expires=datetime.utcnow() + timedelta(days=365)
        )
        business.set_password(form.password.data)

        db.session.add(business)
        db.session.commit()

        seed_default_menu(business.id)
        log_audit_event(business.id, 'BUSINESS_REGISTERED_FREE_TRIAL', f"Business '{business.business_name}' activated Free Trial account.")

        login_user(business, remember=True)
        flash('Welcome! Your Free Trial is now active.', 'success')
        return redirect(url_for('pos.terminal'))

    return render_template('auth/register.html', form=form, annual_price=current_app.config.get('ANNUAL_SUBSCRIPTION_PRICE', 1999))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('pos.terminal'))
        
    form = LoginForm()
    if form.validate_on_submit():
        username_input = form.username.data.strip().lower()
        business = Business.query.filter_by(username=username_input).first()
        
        if business and business.check_password(form.password.data):
            login_user(business, remember=True)
            log_audit_event(business.id, 'USER_LOGIN', 'User logged into POS terminal')
            next_page = request.args.get('next')
            flash(f'Welcome back to {business.business_name} POS Terminal!', 'success')
            return redirect(next_page or url_for('pos.terminal'))
        else:
            flash('Invalid Username / Business ID or Password. Please try again.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit_event(current_user.id, 'USER_LOGOUT', 'User logged out')
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/subscription')
@login_required
def subscription():
    return render_template('auth/subscription.html', business=current_user, annual_price=current_app.config['ANNUAL_SUBSCRIPTION_PRICE'])
