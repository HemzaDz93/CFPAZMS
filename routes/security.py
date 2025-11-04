"""
تعزيزات الأمان - المصادقة الثنائية وSSO
"""

import pyotp
import qrcode
import io
from functools import wraps
from flask import (
    current_app, redirect, url_for, flash, session,
    render_template, request, abort, jsonify
)
from flask_login import current_user, login_required, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from models import db, User, UserMFA, AuditLog

# تهيئة OAuth
oauth = OAuth()

def init_oauth(app):
    """تهيئة موفري SSO"""
    oauth.init_app(app)
    
    # إعداد Google SSO
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'openid email profile'},
    )

    # إعداد Microsoft SSO
    oauth.register(
        name='azure',
        client_id=app.config['AZURE_CLIENT_ID'],
        client_secret=app.config['AZURE_CLIENT_SECRET'],
        access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
        authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        api_base_url='https://graph.microsoft.com/v1.0/',
        client_kwargs={'scope': 'openid email profile'},
    )

def require_mfa(f):
    """مصمم للتحقق من إكمال المصادقة الثنائية"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # التحقق من تفعيل MFA للمستخدم
        user_mfa = UserMFA.query.filter_by(user_id=current_user.id).first()
        if user_mfa and user_mfa.is_enabled:
            if not session.get('mfa_verified'):
                # حفظ URL المقصود
                session['next_url'] = request.url
                return redirect(url_for('auth.verify_mfa'))
        
        return f(*args, **kwargs)
    return decorated_function

def setup_mfa():
    """إعداد المصادقة الثنائية للمستخدم"""
    # إنشاء مفتاح سري جديد
    secret = pyotp.random_base32()
    
    # إنشاء URI TOTP
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        current_user.email,
        issuer_name="CfpaZMS"
    )
    
    # إنشاء رمز QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = img_buffer.getvalue()
    
    return secret, img_str

def verify_totp(secret, token):
    """التحقق من رمز TOTP"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token)

def log_auth_event(user_id, event_type, details, success=True):
    """تسجيل أحداث المصادقة"""
    log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        details=details,
        success=success,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(log)
    db.session.commit()

def check_brute_force(user_id):
    """التحقق من محاولات تسجيل الدخول المتكررة"""
    time_window = 300  # 5 دقائق
    max_attempts = 5
    
    failed_attempts = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.event_type == 'login',
        AuditLog.success == False,
        AuditLog.timestamp >= (db.func.now() - db.text(f'INTERVAL {time_window} SECOND'))
    ).count()
    
    return failed_attempts >= max_attempts

def generate_backup_codes():
    """توليد رموز النسخ الاحتياطية"""
    import secrets
    
    codes = []
    for _ in range(10):
        code = secrets.token_hex(4)
        codes.append(code)
    
    return codes

def hash_backup_codes(codes):
    """تشفير رموز النسخ الاحتياطية"""
    return [generate_password_hash(code) for code in codes]

# مسارات المصادقة الثنائية

@login_required
def setup_mfa_route():
    """مسار إعداد المصادقة الثنائية"""
    # التحقق من عدم تفعيل MFA مسبقاً
    user_mfa = UserMFA.query.filter_by(user_id=current_user.id).first()
    if user_mfa and user_mfa.is_enabled:
        flash('المصادقة الثنائية مفعلة مسبقاً', 'warning')
        return redirect(url_for('auth.security_settings'))
    
    if request.method == 'POST':
        token = request.form.get('token')
        secret = session.get('mfa_secret')
        
        if not secret:
            flash('انتهت صلاحية الجلسة، يرجى المحاولة مرة أخرى', 'error')
            return redirect(url_for('auth.setup_mfa'))
        
        if verify_totp(secret, token):
            # توليد رموز النسخ الاحتياطية
            backup_codes = generate_backup_codes()
            hashed_codes = hash_backup_codes(backup_codes)
            
            # حفظ الإعدادات
            user_mfa = UserMFA(
                user_id=current_user.id,
                secret=secret,
                is_enabled=True,
                backup_codes=hashed_codes
            )
            db.session.add(user_mfa)
            db.session.commit()
            
            # تسجيل الحدث
            log_auth_event(
                current_user.id,
                'mfa_setup',
                'تم تفعيل المصادقة الثنائية بنجاح'
            )
            
            session['backup_codes'] = backup_codes
            return redirect(url_for('auth.show_backup_codes'))
        
        flash('رمز غير صحيح، يرجى المحاولة مرة أخرى', 'error')
        return redirect(url_for('auth.setup_mfa'))
    
    # توليد مفتاح جديد وQR code
    secret, qr_code = setup_mfa()
    session['mfa_secret'] = secret
    
    return render_template(
        'auth/setup_mfa.html',
        qr_code=qr_code
    )

@login_required
def verify_mfa_route():
    """مسار التحقق من المصادقة الثنائية"""
    if request.method == 'POST':
        token = request.form.get('token')
        backup_code = request.form.get('backup_code')
        
        user_mfa = UserMFA.query.filter_by(user_id=current_user.id).first()
        if not user_mfa:
            abort(400)
        
        verified = False
        event_details = ''
        
        if token:
            verified = verify_totp(user_mfa.secret, token)
            event_details = 'تم التحقق باستخدام TOTP'
        elif backup_code:
            # التحقق من رمز النسخ الاحتياطي
            for i, hashed_code in enumerate(user_mfa.backup_codes):
                if check_password_hash(hashed_code, backup_code):
                    # حذف الرمز المستخدم
                    user_mfa.backup_codes.pop(i)
                    db.session.commit()
                    verified = True
                    event_details = 'تم التحقق باستخدام رمز النسخ الاحتياطي'
                    break
        
        if verified:
            session['mfa_verified'] = True
            log_auth_event(current_user.id, 'mfa_verify', event_details)
            next_url = session.pop('next_url', url_for('dashboard.index'))
            return redirect(next_url)
        
        flash('رمز غير صحيح، يرجى المحاولة مرة أخرى', 'error')
        log_auth_event(
            current_user.id,
            'mfa_verify',
            'محاولة تحقق فاشلة',
            success=False
        )
    
    return render_template('auth/verify_mfa.html')

# مسارات SSO

def google_login():
    """تسجيل الدخول باستخدام Google"""
    redirect_uri = url_for('auth.google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

def google_authorize():
    """معالجة استجابة مصادقة Google"""
    try:
        token = oauth.google.authorize_access_token()
        resp = oauth.google.get('userinfo')
        user_info = resp.json()
        
        # البحث عن المستخدم أو إنشاء حساب جديد
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                email=user_info['email'],
                username=user_info['email'].split('@')[0],
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        # تسجيل الدخول
        login_user(user)
        log_auth_event(user.id, 'sso_login', 'تم تسجيل الدخول عبر Google')
        
        return redirect(url_for('dashboard.index'))
    except Exception as e:
        flash('حدث خطأ أثناء تسجيل الدخول، يرجى المحاولة مرة أخرى', 'error')
        log_auth_event(None, 'sso_error', str(e), success=False)
        return redirect(url_for('auth.login'))

def azure_login():
    """تسجيل الدخول باستخدام Microsoft"""
    redirect_uri = url_for('auth.azure_authorize', _external=True)
    return oauth.azure.authorize_redirect(redirect_uri)

def azure_authorize():
    """معالجة استجابة مصادقة Microsoft"""
    try:
        token = oauth.azure.authorize_access_token()
        resp = oauth.azure.get('me')
        user_info = resp.json()
        
        user = User.query.filter_by(email=user_info['mail']).first()
        if not user:
            user = User(
                email=user_info['mail'],
                username=user_info['userPrincipalName'].split('@')[0],
                first_name=user_info.get('givenName', ''),
                last_name=user_info.get('surname', ''),
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        log_auth_event(user.id, 'sso_login', 'تم تسجيل الدخول عبر Microsoft')
        
        return redirect(url_for('dashboard.index'))
    except Exception as e:
        flash('حدث خطأ أثناء تسجيل الدخول، يرجى المحاولة مرة أخرى', 'error')
        log_auth_event(None, 'sso_error', str(e), success=False)
        return redirect(url_for('auth.login'))