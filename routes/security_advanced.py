"""
مسارات الأمان المتقدمة - المرحلة 2
Advanced Security Routes - Phase 2
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required
from models import db, User
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from models.security_enhanced import (
        PasswordPolicy, SecurityAlert, IPWhitelist, AccessKey,
        SecurityLog, RateLimitRule
    )
except ImportError:
    # Fallback untuk jika models belum disetup sebagai package
    import importlib.util
    spec = importlib.util.spec_from_file_location("security_enhanced", 
            os.path.join(os.path.dirname(__file__), '..', 'models', 'security_enhanced.py'))
    security_enhanced = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(security_enhanced)
    PasswordPolicy = security_enhanced.PasswordPolicy
    SecurityAlert = security_enhanced.SecurityAlert
    IPWhitelist = security_enhanced.IPWhitelist
    AccessKey = security_enhanced.AccessKey
    SecurityLog = security_enhanced.SecurityLog
    RateLimitRule = security_enhanced.RateLimitRule
from security_services import (
    PasswordValidator, SessionManager, SecurityAlertService,
    IPSecurityManager, AccessKeyManager, RateLimiter
)
from functools import wraps
from datetime import datetime, timedelta
import json

security_bp = Blueprint('security', __name__, url_prefix='/security')


def admin_required(f):
    """مصمم للتحقق من صلاحيات المسؤول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('يجب أن تكون مسؤولاً للوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


# ============ مسارات سياسة كلمات المرور ============

@security_bp.route('/password-policy', methods=['GET', 'POST'])
@login_required
@admin_required
def password_policy():
    """إدارة سياسة كلمات المرور"""
    policy = PasswordValidator.get_policy()
    
    if request.method == 'POST':
        policy.min_length = int(request.form.get('min_length', 12))
        policy.require_uppercase = request.form.get('require_uppercase') is not None
        policy.require_lowercase = request.form.get('require_lowercase') is not None
        policy.require_numbers = int(request.form.get('require_numbers', 1))
        policy.require_special_chars = int(request.form.get('require_special_chars', 1))
        policy.expiry_days = int(request.form.get('expiry_days', 90))
        policy.history_count = int(request.form.get('history_count', 5))
        policy.lockout_threshold = int(request.form.get('lockout_threshold', 5))
        policy.lockout_duration_minutes = int(request.form.get('lockout_duration_minutes', 30))
        policy.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('تم تحديث سياسة كلمات المرور بنجاح', 'success')
        
        # تسجيل الإجراء
        SecurityLog.log_action(
            user_id=current_user.id,
            action='password_policy_updated',
            resource_type='security',
            new_values={
                'min_length': policy.min_length,
                'expiry_days': policy.expiry_days
            }
        )
    
    return render_template('security/password_policy.html', policy=policy)


# ============ مسارات تنبيهات الأمان ============

@security_bp.route('/alerts', methods=['GET'])
@login_required
@admin_required
def view_alerts():
    """عرض تنبيهات الأمان"""
    page = request.args.get('page', 1, type=int)
    alert_type = request.args.get('type', '')
    severity = request.args.get('severity', '')
    
    query = SecurityAlert.query
    
    if alert_type:
        query = query.filter_by(alert_type=alert_type)
    if severity:
        query = query.filter_by(severity=severity)
    
    alerts = query.order_by(SecurityAlert.created_at.desc()).paginate(page=page, per_page=20)
    
    stats = {
        'total': SecurityAlert.query.count(),
        'unacknowledged': SecurityAlert.query.filter_by(is_acknowledged=False).count(),
        'critical': SecurityAlert.query.filter_by(severity='critical').count(),
    }
    
    return render_template('security/alerts.html', alerts=alerts, stats=stats)


@security_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
@admin_required
def acknowledge_alert(alert_id):
    """الإقرار بتنبيه"""
    alert = SecurityAlert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.id
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم الإقرار بالتنبيه'})


# ============ مسارات مفاتيح الوصول ============

@security_bp.route('/access-keys', methods=['GET'])
@login_required
def access_keys():
    """عرض مفاتيح الوصول الشخصية"""
    user_keys = AccessKey.query.filter_by(user_id=current_user.id).all()
    return render_template('security/access_keys.html', keys=user_keys)


@security_bp.route('/access-keys/create', methods=['GET', 'POST'])
@login_required
def create_access_key():
    """إنشاء مفتاح وصول جديد"""
    if request.method == 'POST':
        key_name = request.form.get('key_name', '').strip()
        expires_days = request.form.get('expires_days', type=int)
        permissions = {
            'read': request.form.get('read_permission') is not None,
            'write': request.form.get('write_permission') is not None,
            'delete': request.form.get('delete_permission') is not None,
        }
        
        if not key_name:
            flash('يجب إدخال اسم المفتاح', 'danger')
            return redirect(url_for('security.create_access_key'))
        
        key, access_key = AccessKeyManager.create_key(
            user_id=current_user.id,
            key_name=key_name,
            permissions=permissions,
            expires_days=expires_days
        )
        
        flash('تم إنشاء المفتاح بنجاح. احفظ هذا المفتاح في مكان آمن!', 'success')
        return render_template('security/key_created.html', key=key, access_key=access_key)
    
    return render_template('security/create_access_key.html')


@security_bp.route('/access-keys/<int:key_id>/revoke', methods=['POST'])
@login_required
def revoke_access_key(key_id):
    """إلغاء مفتاح الوصول"""
    access_key = AccessKey.query.get(key_id)
    
    if not access_key or access_key.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    success = AccessKeyManager.revoke_key(key_id)
    if success:
        flash('تم إلغاء المفتاح بنجاح', 'success')
    
    return redirect(url_for('security.access_keys'))


# ============ مسارات قائمة IP الموثوقة ============

@security_bp.route('/trusted-ips', methods=['GET'])
@login_required
def trusted_ips():
    """عرض قائمة عناوين IP الموثوقة"""
    user_ips = IPWhitelist.query.filter_by(user_id=current_user.id).all()
    return render_template('security/trusted_ips.html', ips=user_ips)


@security_bp.route('/trusted-ips/add', methods=['GET', 'POST'])
@login_required
def add_trusted_ip():
    """إضافة عنوان IP موثوق"""
    if request.method == 'POST':
        ip_address = request.form.get('ip_address', '').strip()
        device_name = request.form.get('device_name', '').strip()
        expires_days = request.form.get('expires_days', type=int) or 90
        
        if not ip_address:
            flash('يجب إدخال عنوان IP', 'danger')
            return redirect(url_for('security.add_trusted_ip'))
        
        # التحقق من صحة عنوان IP
        import ipaddress
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            flash('عنوان IP غير صحيح', 'danger')
            return redirect(url_for('security.add_trusted_ip'))
        
        whitelist = IPSecurityManager.add_to_whitelist(
            user_id=current_user.id,
            ip_address=ip_address,
            device_name=device_name,
            expires_days=expires_days
        )
        
        flash('تم إضافة عنوان IP الموثوق بنجاح', 'success')
        return redirect(url_for('security.trusted_ips'))
    
    return render_template('security/add_trusted_ip.html')


@security_bp.route('/trusted-ips/<int:ip_id>/remove', methods=['POST'])
@login_required
def remove_trusted_ip(ip_id):
    """إزالة عنوان IP موثوق"""
    whitelist = IPWhitelist.query.get(ip_id)
    
    if not whitelist or whitelist.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    whitelist.is_active = False
    db.session.commit()
    
    flash('تم إزالة عنوان IP الموثوق', 'success')
    return redirect(url_for('security.trusted_ips'))


# ============ مسارات سجل الأمان ============

@security_bp.route('/audit-log', methods=['GET'])
@login_required
def audit_log():
    """عرض سجل الأمان"""
    if current_user.role != 'admin':
        # المستخدم العادي يرى فقط سجله الخاص
        logs = SecurityLog.query.filter_by(user_id=current_user.id).order_by(
            SecurityLog.timestamp.desc()
        ).paginate(page=request.args.get('page', 1, type=int), per_page=20)
    else:
        # المسؤول يرى جميع السجلات
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action', '')
        
        query = SecurityLog.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        if action:
            query = query.filter_by(action=action)
        
        logs = query.order_by(SecurityLog.timestamp.desc()).paginate(
            page=request.args.get('page', 1, type=int), per_page=20
        )
    
    return render_template('security/audit_log.html', logs=logs)


# ============ مسارات إدارة معدل الطلبات ============

@security_bp.route('/rate-limits', methods=['GET'])
@login_required
@admin_required
def rate_limits():
    """عرض قواعد معدل الطلبات"""
    rules = RateLimitRule.query.all()
    return render_template('security/rate_limits.html', rules=rules)


@security_bp.route('/rate-limits/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_rate_limit():
    """إنشاء قاعدة معدل طلبات جديدة"""
    if request.method == 'POST':
        endpoint = request.form.get('endpoint', '').strip()
        method = request.form.get('method', 'GET').upper()
        requests_per_minute = int(request.form.get('requests_per_minute', 60))
        requests_per_hour = int(request.form.get('requests_per_hour', 1000))
        
        rule = RateLimitRule(
            endpoint=endpoint,
            method=method,
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour
        )
        db.session.add(rule)
        db.session.commit()
        
        flash('تم إنشاء قاعدة معدل الطلبات بنجاح', 'success')
        return redirect(url_for('security.rate_limits'))
    
    return render_template('security/create_rate_limit.html')


@security_bp.route('/rate-limits/<int:rule_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_rate_limit(rule_id):
    """تحرير قاعدة معدل طلبات"""
    rule = RateLimitRule.query.get(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404
    
    if request.method == 'POST':
        rule.requests_per_minute = int(request.form.get('requests_per_minute', 60))
        rule.requests_per_hour = int(request.form.get('requests_per_hour', 1000))
        rule.is_enabled = request.form.get('is_enabled') is not None
        rule.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('تم تحديث قاعدة معدل الطلبات بنجاح', 'success')
        return redirect(url_for('security.rate_limits'))
    
    return render_template('security/edit_rate_limit.html', rule=rule)


# ============ مسارات الإحصائيات والتقارير ============

@security_bp.route('/dashboard', methods=['GET'])
@login_required
@admin_required
def security_dashboard():
    """لوحة تحكم الأمان"""
    
    # الإحصائيات العامة
    stats = {
        'total_users': User.query.count(),
        'active_sessions': db.session.query(db.func.count(SecurityLog.query.filter_by(action='login'))).scalar(),
        'failed_logins_today': SecurityLog.query.filter(
            SecurityLog.action == 'login',
            SecurityLog.status == 'failed',
            SecurityLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count(),
        'alerts_today': SecurityAlert.query.filter(
            SecurityAlert.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count(),
        'critical_alerts': SecurityAlert.query.filter_by(
            severity='critical',
            is_acknowledged=False
        ).count(),
    }
    
    # آخر التنبيهات
    recent_alerts = SecurityAlert.query.order_by(
        SecurityAlert.created_at.desc()
    ).limit(10).all()
    
    # آخر محاولات الدخول الفاشلة
    failed_logins = SecurityLog.query.filter(
        SecurityLog.action == 'login',
        SecurityLog.status == 'failed',
        SecurityLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).order_by(SecurityLog.timestamp.desc()).limit(10).all()
    
    # توزيع التنبيهات حسب النوع
    alert_types = db.session.query(
        SecurityAlert.alert_type,
        db.func.count(SecurityAlert.id)
    ).filter(
        SecurityAlert.created_at >= datetime.utcnow() - timedelta(days=7)
    ).group_by(SecurityAlert.alert_type).all()
    
    alert_stats = {alert_type: count for alert_type, count in alert_types}
    
    return render_template(
        'security/dashboard.html',
        stats=stats,
        recent_alerts=recent_alerts,
        failed_logins=failed_logins,
        alert_stats=alert_stats
    )


# ============ مسارات API الأمان ============

@security_bp.route('/api/password-strength', methods=['POST'])
@login_required
def check_password_strength():
    """التحقق من قوة كلمة المرور (API)"""
    password = request.json.get('password', '')
    policy = PasswordValidator.get_policy()
    
    is_valid, errors = PasswordValidator.validate_password(password, policy)
    
    # حساب نقاط القوة
    strength = 0
    if len(password) >= policy.min_length:
        strength += 25
    if re.search(r'[A-Z]', password) and policy.require_uppercase:
        strength += 25
    if re.search(r'[a-z]', password) and policy.require_lowercase:
        strength += 25
    if re.search(r'[0-9]', password) and policy.require_numbers:
        strength += 25
    
    return jsonify({
        'valid': is_valid,
        'errors': errors,
        'strength': min(strength, 100),
        'requirements': {
            'min_length': f'{policy.min_length} أحرف',
            'uppercase': 'أحرف كبيرة' if policy.require_uppercase else 'اختياري',
            'lowercase': 'أحرف صغيرة' if policy.require_lowercase else 'اختياري',
            'numbers': f'{policy.require_numbers} أرقام' if policy.require_numbers else 'اختياري',
            'special_chars': f'{policy.require_special_chars} أحرف خاصة' if policy.require_special_chars else 'اختياري',
        }
    })


@security_bp.route('/api/session-info', methods=['GET'])
@login_required
def session_info():
    """الحصول على معلومات الجلسة (API)"""
    return jsonify({
        'user_id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'session_token_count': SessionToken.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).count(),
        'active_keys': AccessKey.query.filter(
            AccessKey.user_id == current_user.id,
            AccessKey.is_active == True,
            AccessKey.revoked_at == None
        ).count(),
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
    })


import re