"""
خدمات الأمان المتقدمة - المرحلة 2
Advanced Security Services - Phase 2
"""

import re
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, abort, current_app, session, jsonify
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import sys
import os
import importlib.util

# Dynamic import for security_enhanced models
try:
    from models.security_enhanced import (
        PasswordPolicy, PasswordHistory, SessionToken, SecurityAlert,
        IPWhitelist, AccessKey, SecurityLog, DataEncryption,
        ComplianceRecord, RateLimitRule, RateLimitViolation
    )
except ImportError:
    spec = importlib.util.spec_from_file_location("security_enhanced", 
            os.path.join(os.path.dirname(__file__), 'models', 'security_enhanced.py'))
    security_enhanced = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(security_enhanced)
    PasswordPolicy = security_enhanced.PasswordPolicy
    PasswordHistory = security_enhanced.PasswordHistory
    SessionToken = security_enhanced.SessionToken
    SecurityAlert = security_enhanced.SecurityAlert
    IPWhitelist = security_enhanced.IPWhitelist
    AccessKey = security_enhanced.AccessKey
    SecurityLog = security_enhanced.SecurityLog
    DataEncryption = security_enhanced.DataEncryption
    ComplianceRecord = security_enhanced.ComplianceRecord
    RateLimitRule = security_enhanced.RateLimitRule
    RateLimitViolation = security_enhanced.RateLimitViolation
import hmac


class PasswordValidator:
    """مدقق كلمات المرور"""
    
    @staticmethod
    def get_policy():
        """الحصول على سياسة كلمات المرور الحالية"""
        policy = PasswordPolicy.query.first()
        if not policy:
            policy = PasswordPolicy()
            db.session.add(policy)
            db.session.commit()
        return policy
    
    @staticmethod
    def validate_password(password, policy=None):
        """التحقق من قوة كلمة المرور"""
        if policy is None:
            policy = PasswordValidator.get_policy()
        
        errors = []
        
        # التحقق من الطول الأدنى
        if len(password) < policy.min_length:
            errors.append(f'كلمة المرور يجب أن تكون {policy.min_length} أحرف على الأقل')
        
        # التحقق من الأحرف الكبيرة
        if policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append('كلمة المرور يجب أن تحتوي على أحرف كبيرة')
        
        # التحقق من الأحرف الصغيرة
        if policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append('كلمة المرور يجب أن تحتوي على أحرف صغيرة')
        
        # التحقق من الأرقام
        if policy.require_numbers and len(re.findall(r'[0-9]', password)) < policy.require_numbers:
            errors.append(f'كلمة المرور يجب أن تحتوي على {policy.require_numbers} أرقام على الأقل')
        
        # التحقق من الأحرف الخاصة
        special_chars = re.findall(r'[!@#$%^&*()_+=\[\]{};:\'",.<>?/\\|`~-]', password)
        if policy.require_special_chars and len(special_chars) < policy.require_special_chars:
            errors.append(f'كلمة المرور يجب أن تحتوي على {policy.require_special_chars} أحرف خاصة على الأقل')
        
        return len(errors) == 0, errors
    
    @staticmethod
    def check_password_history(user_id, new_password, policy=None):
        """التحقق من عدم تكرار كلمات المرور السابقة"""
        if policy is None:
            policy = PasswordValidator.get_policy()
        
        # الحصول على آخر N كلمات مرور
        history = PasswordHistory.query.filter_by(user_id=user_id).order_by(
            PasswordHistory.changed_at.desc()
        ).limit(policy.history_count).all()
        
        for record in history:
            if check_password_hash(record.password_hash, new_password):
                return False, f'لا يمكنك استخدام واحدة من آخر {policy.history_count} كلمات مرور'
        
        return True, None
    
    @staticmethod
    def set_password(user, new_password, changed_by=None):
        """تعيين كلمة مرور جديدة مع التسجيل في السجل"""
        user.set_password(new_password)
        
        # تسجيل في السجل
        history = PasswordHistory(
            user_id=user.id,
            password_hash=user.password_hash,
            changed_by=changed_by or request.remote_addr
        )
        db.session.add(history)
        db.session.commit()
        
        # تسجيل في سجل الأمان
        SecurityLog.log_action(
            user_id=user.id,
            action='password_change',
            status='success',
            ip_address=request.remote_addr
        )
        
        return True


class SessionManager:
    """مدير الجلسات"""
    
    @staticmethod
    def create_session(user_id, ip_address=None, user_agent=None, device_fingerprint=None):
        """إنشاء جلسة جديدة"""
        if ip_address is None:
            ip_address = request.remote_addr
        if user_agent is None:
            user_agent = request.user_agent.string
        
        # إلغاء الجلسات القديمة
        old_sessions = SessionToken.query.filter_by(user_id=user_id, is_active=True).all()
        for old_session in old_sessions:
            if (datetime.utcnow() - old_session.last_activity).seconds > 3600:  # أكثر من ساعة
                old_session.is_active = False
        
        # إنشاء جلسة جديدة
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        session_token = SessionToken(
            user_id=user_id,
            token=token,
            token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(session_token)
        db.session.commit()
        
        return token
    
    @staticmethod
    def validate_session(token_hash, ip_address=None):
        """التحقق من صحة الجلسة"""
        session_token = SessionToken.query.filter_by(token_hash=token_hash).first()
        
        if not session_token or not session_token.is_valid():
            return None
        
        # التحقق من عنوان IP إذا كان مختلفاً
        if ip_address and ip_address != session_token.ip_address:
            # إنشاء تنبيه أمان
            alert = SecurityAlert(
                user_id=session_token.user_id,
                alert_type='ip_change',
                severity='medium',
                title='تغيير عنوان IP',
                description=f'تم الكشف عن تغيير في عنوان IP من {session_token.ip_address} إلى {ip_address}',
                ip_address=ip_address
            )
            db.session.add(alert)
            db.session.commit()
        
        # تحديث آخر نشاط
        session_token.last_activity = datetime.utcnow()
        db.session.commit()
        
        return session_token
    
    @staticmethod
    def revoke_session(token_hash):
        """إلغاء جلسة"""
        session_token = SessionToken.query.filter_by(token_hash=token_hash).first()
        if session_token:
            session_token.is_active = False
            session_token.revoked_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def revoke_all_sessions(user_id):
        """إلغاء جميع جلسات المستخدم"""
        sessions = SessionToken.query.filter_by(user_id=user_id, is_active=True).all()
        for session_token in sessions:
            session_token.is_active = False
            session_token.revoked_at = datetime.utcnow()
        db.session.commit()
        return len(sessions)


class SecurityAlertService:
    """خدمة تنبيهات الأمان"""
    
    @staticmethod
    def create_alert(user_id=None, alert_type='unusual_activity', severity='low',
                     title='', description='', ip_address=None, user_agent=None, metadata=None):
        """إنشاء تنبيه أمان"""
        
        alert = SecurityAlert(
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            ip_address=ip_address or request.remote_addr,
            user_agent=user_agent or request.user_agent.string,
            metadata=metadata or {}
        )
        db.session.add(alert)
        db.session.commit()
        
        # تسجيل في الأمان
        SecurityLog.log_action(
            user_id=user_id,
            action='security_alert_created',
            details={
                'alert_type': alert_type,
                'severity': severity
            }
        )
        
        return alert
    
    @staticmethod
    def acknowledge_alert(alert_id, user_id):
        """الإقرار بتنبيه"""
        alert = SecurityAlert.query.get(alert_id)
        if alert:
            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = user_id
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_critical_alerts(limit=10):
        """الحصول على التنبيهات الحرجة"""
        return SecurityAlert.query.filter_by(severity='critical', is_acknowledged=False).order_by(
            SecurityAlert.created_at.desc()
        ).limit(limit).all()


class IPSecurityManager:
    """مدير أمان عناوين IP"""
    
    @staticmethod
    def is_ip_whitelisted(user_id, ip_address, device_fingerprint=None):
        """التحقق من أن عنوان IP موثوق"""
        whitelist = IPWhitelist.query.filter_by(
            user_id=user_id,
            ip_address=ip_address,
            is_active=True
        ).first()
        
        if whitelist and whitelist.is_valid():
            whitelist.last_used_at = datetime.utcnow()
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def add_to_whitelist(user_id, ip_address, device_name=None, device_fingerprint=None, expires_days=90):
        """إضافة عنوان IP إلى قائمة الموثوقة"""
        whitelist = IPWhitelist(
            user_id=user_id,
            ip_address=ip_address,
            device_name=device_name,
            device_fingerprint=device_fingerprint,
            expires_at=datetime.utcnow() + timedelta(days=expires_days)
        )
        db.session.add(whitelist)
        db.session.commit()
        return whitelist
    
    @staticmethod
    def detect_suspicious_login(user_id, ip_address):
        """كشف محاولات دخول مريبة"""
        # البحث عن محاولات دخول من عنوان IP غير معروف
        if not IPSecurityManager.is_ip_whitelisted(user_id, ip_address):
            # البحث عن محاولات دخول أخرى من نفس الـ IP
            recent_attempts = SecurityLog.query.filter(
                SecurityLog.user_id != user_id,
                SecurityLog.ip_address == ip_address,
                SecurityLog.action.in_(['login', 'failed_login']),
                SecurityLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_attempts > 5:
                return True, 'Multiple failed login attempts detected'
        
        return False, None


class AccessKeyManager:
    """مدير مفاتيح الوصول"""
    
    @staticmethod
    def create_key(user_id, key_name, permissions=None, expires_days=None):
        """إنشاء مفتاح وصول جديد"""
        key, key_hash, key_prefix = AccessKey.generate_key()
        
        access_key = AccessKey(
            user_id=user_id,
            key_name=key_name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions or {},
            expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
            created_by_ip=request.remote_addr
        )
        db.session.add(access_key)
        db.session.commit()
        
        # تسجيل في الأمان
        SecurityLog.log_action(
            user_id=user_id,
            action='key_generated',
            details={'key_name': key_name, 'key_prefix': key_prefix}
        )
        
        return key, access_key
    
    @staticmethod
    def verify_key(key):
        """التحقق من صحة مفتاح الوصول"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        access_key = AccessKey.query.filter_by(key_hash=key_hash).first()
        
        if access_key and access_key.is_valid():
            access_key.last_used_at = datetime.utcnow()
            db.session.commit()
            return access_key
        
        return None
    
    @staticmethod
    def revoke_key(key_id):
        """إلغاء مفتاح الوصول"""
        access_key = AccessKey.query.get(key_id)
        if access_key:
            access_key.revoked_at = datetime.utcnow()
            db.session.commit()
            
            # تسجيل في الأمان
            SecurityLog.log_action(
                user_id=access_key.user_id,
                action='key_revoked',
                details={'key_name': access_key.key_name}
            )
            
            return True
        return False


class SecurityLog:
    """سجل الأمان الثابت"""
    
    @staticmethod
    def log_action(user_id=None, action='', resource_type=None, resource_id=None,
                   old_values=None, new_values=None, status='success',
                   error_message=None, ip_address=None, details=None):
        """تسجيل إجراء أمني"""
        from models.security_enhanced import SecurityLog as SecurityLogModel
        
        log = SecurityLogModel(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address or request.remote_addr,
            user_agent=request.user_agent.string,
            status=status,
            error_message=error_message
        )
        db.session.add(log)
        db.session.commit()
        return log


class RateLimiter:
    """محدد معدل الطلبات"""
    
    @staticmethod
    def check_rate_limit(endpoint, user_id=None, ip_address=None):
        """التحقق من معدل الطلبات"""
        if ip_address is None:
            ip_address = request.remote_addr
        
        rule = RateLimitRule.query.filter_by(endpoint=endpoint, is_enabled=True).first()
        if not rule:
            return True, None
        
        # التحقق من الأدوار المستثناة
        if current_user.is_authenticated and current_user.role in rule.bypass_roles:
            return True, None
        
        # حساب عدد الطلبات في آخر دقيقة
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_requests = RateLimitViolation.query.filter(
            RateLimitViolation.ip_address == ip_address,
            RateLimitViolation.endpoint == endpoint,
            RateLimitViolation.timestamp >= one_minute_ago
        ).count()
        
        if recent_requests >= rule.requests_per_minute:
            # تسجيل الانتهاك
            violation = RateLimitViolation(
                user_id=user_id,
                ip_address=ip_address,
                endpoint=endpoint,
                request_count=recent_requests + 1,
                action_taken='blocked'
            )
            db.session.add(violation)
            db.session.commit()
            
            return False, 'Rate limit exceeded'
        
        return True, None


def require_secure_password(f):
    """مصمم للتحقق من كلمة مرور قوية"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        password = request.form.get('password', '') or request.json.get('password', '')
        policy = PasswordValidator.get_policy()
        is_valid, errors = PasswordValidator.validate_password(password, policy)
        
        if not is_valid:
            return jsonify({'errors': errors}), 400
        
        return f(*args, **kwargs)
    return decorated_function


def check_rate_limit(endpoint):
    """مصمم لفحص معدل الطلبات"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_allowed, error = RateLimiter.check_rate_limit(endpoint)
            if not is_allowed:
                abort(429)  # Too Many Requests
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_security_action(action, resource_type=None):
    """مصمم لتسجيل الإجراءات الأمنية"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                SecurityLog.log_action(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    action=action,
                    resource_type=resource_type,
                    status='success'
                )
                return result
            except Exception as e:
                SecurityLog.log_action(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    action=action,
                    resource_type=resource_type,
                    status='failed',
                    error_message=str(e)
                )
                raise
        return decorated_function
    return decorator