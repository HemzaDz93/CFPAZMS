"""
Middleware الأمان - الحماية من الهجمات والتحقق من معدل الطلبات
Security Middleware - Attack Prevention & Rate Limiting
"""

from flask import request, abort, jsonify, current_app
from functools import wraps
from datetime import datetime, timedelta
from models import db
import hashlib
import re
from urllib.parse import urlparse
import os
import importlib.util

# Dynamic import for security_enhanced models
try:
    from models.security_enhanced import RateLimitViolation, SecurityAlert, SecurityLog
except ImportError:
    spec = importlib.util.spec_from_file_location("security_enhanced", 
            os.path.join(os.path.dirname(__file__), 'models', 'security_enhanced.py'))
    security_enhanced = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(security_enhanced)
    RateLimitViolation = security_enhanced.RateLimitViolation
    SecurityAlert = security_enhanced.SecurityAlert
    SecurityLog = security_enhanced.SecurityLog


class SecurityHeaders:
    """إضافة رؤوس أمان إلى جميع الاستجابات"""
    
    @staticmethod
    def apply_headers(response):
        """تطبيق رؤوس الأمان"""
        # منع Click-jacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # منع MIME-type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # تفعيل XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # سياسة محتوى أمان
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' cdn.jsdelivr.net; "
            "connect-src 'self'"
        )
        
        # سياسة الإحالة
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS (ملقم معين - استخدم في الإنتاج فقط)
        if not current_app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # منع الوصول إلى المتغيرات الشخصية
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
        
        return response


class RateLimitMiddleware:
    """Middleware لتحديد معدل الطلبات"""
    
    # تخزين مؤقت للطلبات (في الإنتاج يجب استخدام Redis)
    _request_cache = {}
    
    @staticmethod
    def check_rate_limit():
        """فحص معدل الطلبات"""
        if not current_app.config.get('RATE_LIMIT_ENABLED', True):
            return True
        
        # الحصول على معرف فريد (IP أو User)
        client_id = request.remote_addr
        
        # الحصول على الفترة الزمنية الحالية (دقيقة)
        current_minute = datetime.utcnow().replace(second=0, microsecond=0)
        
        # مفتاح الذاكرة المؤقتة
        cache_key = f"{client_id}:{current_minute.isoformat()}"
        
        # زيادة عدد الطلبات
        if cache_key not in RateLimitMiddleware._request_cache:
            RateLimitMiddleware._request_cache[cache_key] = 0
        
        RateLimitMiddleware._request_cache[cache_key] += 1
        
        # التحقق من الحد
        limit = current_app.config.get('RATE_LIMIT_DEFAULT_PER_MINUTE', 60)
        
        if RateLimitMiddleware._request_cache[cache_key] > limit:
            # تسجيل الانتهاك
            violation = RateLimitViolation(
                ip_address=client_id,
                endpoint=request.endpoint,
                request_count=RateLimitMiddleware._request_cache[cache_key],
                action_taken='blocked'
            )
            db.session.add(violation)
            db.session.commit()
            
            return False
        
        return True


class InputSanitizer:
    """تنظيف وتحقق من المدخلات"""
    
    @staticmethod
    def sanitize_input(data):
        """تنظيف المدخلات من الهجمات XSS"""
        if isinstance(data, str):
            # إزالة السكريبتات الضارة
            dangerous_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'<iframe[^>]*>',
                r'<embed[^>]*>',
                r'<object[^>]*>',
            ]
            
            for pattern in dangerous_patterns:
                data = re.sub(pattern, '', data, flags=re.IGNORECASE | re.DOTALL)
            
            return data
        elif isinstance(data, dict):
            return {key: InputSanitizer.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [InputSanitizer.sanitize_input(item) for item in data]
        
        return data
    
    @staticmethod
    def validate_url(url):
        """التحقق من صحة URL"""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False


class SQLInjectionProtection:
    """حماية من هجمات SQL Injection"""
    
    # كلمات مفتاحية خطرة
    DANGEROUS_KEYWORDS = [
        'UNION', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP',
        'CREATE', 'ALTER', 'EXEC', 'EXECUTE', ';', '--', '/*', '*/',
        'xp_', 'sp_'
    ]
    
    @staticmethod
    def check_sql_injection(data):
        """فحص للعثور على محاولات SQL Injection"""
        if isinstance(data, str):
            data_upper = data.upper()
            for keyword in SQLInjectionProtection.DANGEROUS_KEYWORDS:
                if keyword in data_upper:
                    return True
        elif isinstance(data, dict):
            for value in data.values():
                if SQLInjectionProtection.check_sql_injection(value):
                    return True
        
        return False


class AuditTrailMiddleware:
    """تسجيل مسار التدقيق الكامل"""
    
    @staticmethod
    def log_request(response):
        """تسجيل معلومات الطلب"""
        # تجاهل الطلبات الثابتة
        if request.path.startswith('/static/') or request.path.endswith('.css') or request.path.endswith('.js'):
            return response
        
        if not current_app.config.get('AUDIT_LOGGING_ENABLED', True):
            return response
        
        try:
            from flask_login import current_user
            
            # تسجيل الطلبات المهمة فقط
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                SecurityLog.log_action(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    action='request',
                    details={
                        'method': request.method,
                        'endpoint': request.endpoint,
                        'path': request.path,
                    },
                    ip_address=request.remote_addr,
                    status='success'
                )
        except Exception as e:
            current_app.logger.error(f'Error logging request: {str(e)}')
        
        return response


class CSRFProtection:
    """حماية من هجمات CSRF"""
    
    # الطرق الآمنة التي لا تحتاج إلى تحقق CSRF
    SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS', 'TRACE']
    
    # Endpoints التي لا تحتاج CSRF token
    EXCLUDED_ENDPOINTS = [
        'auth.login',
        'auth.logout',
        'api.health_check'
    ]
    
    @staticmethod
    def validate_csrf_token():
        """التحقق من توكن CSRF"""
        if request.method in CSRFProtection.SAFE_METHODS:
            return True
        
        if request.endpoint in CSRFProtection.EXCLUDED_ENDPOINTS:
            return True
        
        # API requests
        if request.path.startswith('/api/'):
            token = request.headers.get('X-CSRF-Token')
        else:
            token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
        
        if not token:
            return False
        
        # التحقق من صحة التوكن
        session_token = request.cookies.get('csrf_token')
        if not session_token:
            return False
        
        # التحقق من التوكن (في الإنتاج استخدم library متخصصة)
        return hashlib.sha256(token.encode()).hexdigest() == session_token


def init_security_middleware(app):
    """تهيئة middleware الأمان"""
    
    # تطبيق رؤوس الأمان
    @app.after_request
    def apply_security_headers(response):
        return SecurityHeaders.apply_headers(response)
    
    # فحص معدل الطلبات
    @app.before_request
    def check_rate_limit():
        if not RateLimitMiddleware.check_rate_limit():
            abort(429)  # Too Many Requests
    
    # فحص الحقن
    @app.before_request
    def check_injection_attacks():
        # فحص SQL Injection
        if SQLInjectionProtection.check_sql_injection(request.args):
            SecurityAlert.create_alert(
                alert_type='suspicious_activity',
                severity='high',
                title='محاولة هجوم SQL Injection محتملة',
                description=f'تم اكتشاف محاولة SQL Injection من {request.remote_addr}',
                ip_address=request.remote_addr
            )
            abort(400)
        
        # تنظيف المدخلات
        request.sanitized_data = InputSanitizer.sanitize_input(request.form.to_dict())
    
    # تسجيل سجل التدقيق
    @app.after_request
    def log_audit_trail(response):
        return AuditTrailMiddleware.log_request(response)
    
    app.logger.info('Security middleware initialized successfully')


def security_required(f):
    """مصمم للتحقق من الحد الأدنى من متطلبات الأمان"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # فحص معدل الطلبات
        if not RateLimitMiddleware.check_rate_limit():
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # فحص CSRF
        if not CSRFProtection.validate_csrf_token():
            return jsonify({'error': 'CSRF token validation failed'}), 403
        
        return f(*args, **kwargs)
    return decorated_function