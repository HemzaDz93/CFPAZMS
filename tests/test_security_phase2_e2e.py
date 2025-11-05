"""
اختبارات E2E للمرحلة 2 من نظام الأمان
End-to-End Tests for Security Phase 2
"""

import pytest
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from app import create_app
from models import db, User
from models.security_enhanced import (
    PasswordPolicy, SecurityAlert, IPWhitelist, AccessKey, SecurityLog
)
from datetime import datetime, timedelta
import re


@pytest.fixture(scope="session")
def app():
    """إنشاء تطبيق اختبار"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    """عميل الاختبار"""
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    """منفذ أوامر CLI"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """إنشاء مستخدم اختبار"""
    with app.app_context():
        user = User(
            username='testuser',
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            role='admin',
            is_active=True
        )
        user.set_password('TestPassword123!')
        db.session.add(user)
        db.session.commit()
        return user


class TestPasswordPolicy:
    """اختبارات سياسة كلمات المرور"""

    def test_weak_password_validation(self, app):
        """اختبار رفض كلمات المرور الضعيفة"""
        with app.app_context():
            from security_services import PasswordValidator
            
            weak_passwords = [
                '123456',           # قصيرة جداً
                'password',         # لا تحتوي على أرقام
                'PASSWORD',         # لا تحتوي على أحرف صغيرة
                'Password',         # لا تحتوي على أرقام أو أحرف خاصة
                'Pass123',          # قصيرة جداً
            ]
            
            policy = PasswordValidator.get_policy()
            
            for password in weak_passwords:
                is_valid, errors = PasswordValidator.validate_password(password, policy)
                assert not is_valid
                assert len(errors) > 0

    def test_strong_password_validation(self, app):
        """اختبار قبول كلمات المرور القوية"""
        with app.app_context():
            from security_services import PasswordValidator
            
            strong_passwords = [
                'TestPassword123!',
                'SecurePass@2024',
                'MyStr0ngPwd#',
                'Complex!Pass123'
            ]
            
            policy = PasswordValidator.get_policy()
            
            for password in strong_passwords:
                is_valid, errors = PasswordValidator.validate_password(password, policy)
                assert is_valid
                assert len(errors) == 0

    def test_password_policy_creation(self, app):
        """اختبار إنشاء سياسة كلمات المرور"""
        with app.app_context():
            policy = PasswordPolicy(
                min_length=14,
                require_uppercase=True,
                require_lowercase=True,
                require_numbers=2,
                require_special_chars=2
            )
            db.session.add(policy)
            db.session.commit()
            
            assert policy.id is not None
            assert policy.min_length == 14
            assert policy.require_numbers == 2


class TestSessionManagement:
    """اختبارات إدارة الجلسات"""

    def test_session_creation(self, app, test_user):
        """اختبار إنشاء جلسة"""
        with app.app_context():
            from security_services import SessionManager
            
            token = SessionManager.create_session(test_user.id)
            
            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0

    def test_session_validation(self, app, test_user):
        """اختبار التحقق من صحة الجلسة"""
        with app.app_context():
            from security_services import SessionManager
            import hashlib
            
            token = SessionManager.create_session(test_user.id)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            session = SessionManager.validate_session(token_hash)
            
            assert session is not None
            assert session.user_id == test_user.id
            assert session.is_active

    def test_session_revocation(self, app, test_user):
        """اختبار إلغاء الجلسة"""
        with app.app_context():
            from security_services import SessionManager
            import hashlib
            
            token = SessionManager.create_session(test_user.id)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # إلغاء الجلسة
            success = SessionManager.revoke_session(token_hash)
            assert success
            
            # التحقق من عدم صحة الجلسة
            session = SessionManager.validate_session(token_hash)
            assert session is None

    def test_session_expiration(self, app, test_user):
        """اختبار انتهاء صلاحية الجلسة"""
        with app.app_context():
            from security_services import SessionManager
            from models.security_enhanced import SessionToken
            import hashlib
            
            token = SessionManager.create_session(test_user.id)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # جعل الجلسة منتهية الصلاحية
            session = SessionToken.query.filter_by(token_hash=token_hash).first()
            session.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            # التحقق من عدم صحة الجلسة
            session = SessionManager.validate_session(token_hash)
            assert session is None


class TestAccessKeys:
    """اختبارات مفاتيح الوصول"""

    def test_access_key_creation(self, app, test_user):
        """اختبار إنشاء مفتاح وصول"""
        with app.app_context():
            from security_services import AccessKeyManager
            
            key, access_key = AccessKeyManager.create_key(
                user_id=test_user.id,
                key_name='Test API Key',
                permissions={'read': True, 'write': False}
            )
            
            assert key is not None
            assert access_key.id is not None
            assert access_key.key_name == 'Test API Key'
            assert access_key.permissions['read'] is True

    def test_access_key_verification(self, app, test_user):
        """اختبار التحقق من مفتاح الوصول"""
        with app.app_context():
            from security_services import AccessKeyManager
            
            key, access_key = AccessKeyManager.create_key(
                user_id=test_user.id,
                key_name='Verification Test'
            )
            
            verified_key = AccessKeyManager.verify_key(key)
            
            assert verified_key is not None
            assert verified_key.id == access_key.id

    def test_access_key_revocation(self, app, test_user):
        """اختبار إلغاء مفتاح الوصول"""
        with app.app_context():
            from security_services import AccessKeyManager
            
            key, access_key = AccessKeyManager.create_key(
                user_id=test_user.id,
                key_name='Revocation Test'
            )
            
            success = AccessKeyManager.revoke_key(access_key.id)
            assert success
            
            # التحقق من عدم صحة المفتاح
            verified_key = AccessKeyManager.verify_key(key)
            assert verified_key is None


class TestSecurityAlerts:
    """اختبارات تنبيهات الأمان"""

    def test_alert_creation(self, app, test_user):
        """اختبار إنشاء تنبيه"""
        with app.app_context():
            from security_services import SecurityAlertService
            
            alert = SecurityAlertService.create_alert(
                user_id=test_user.id,
                alert_type='suspicious_login',
                severity='high',
                title='محاولة دخول مريبة',
                description='اكتشفنا محاولة دخول من عنوان IP جديد'
            )
            
            assert alert.id is not None
            assert alert.user_id == test_user.id
            assert alert.severity == 'high'

    def test_alert_acknowledgment(self, app, test_user):
        """اختبار الإقرار بالتنبيه"""
        with app.app_context():
            from security_services import SecurityAlertService
            
            alert = SecurityAlertService.create_alert(
                user_id=test_user.id,
                alert_type='account_lockout'
            )
            
            success = SecurityAlertService.acknowledge_alert(alert.id, test_user.id)
            assert success
            
            from models.security_enhanced import SecurityAlert
            acknowledged_alert = SecurityAlert.query.get(alert.id)
            assert acknowledged_alert.is_acknowledged


class TestIPWhitelist:
    """اختبارات قائمة IP الموثوقة"""

    def test_add_whitelist_ip(self, app, test_user):
        """اختبار إضافة عنوان IP موثوق"""
        with app.app_context():
            from security_services import IPSecurityManager
            
            whitelist = IPSecurityManager.add_to_whitelist(
                user_id=test_user.id,
                ip_address='192.168.1.1',
                device_name='Home PC'
            )
            
            assert whitelist.id is not None
            assert whitelist.ip_address == '192.168.1.1'

    def test_check_whitelisted_ip(self, app, test_user):
        """اختبار التحقق من عنوان IP الموثوق"""
        with app.app_context():
            from security_services import IPSecurityManager
            
            # إضافة عنوان موثوق
            IPSecurityManager.add_to_whitelist(
                user_id=test_user.id,
                ip_address='10.0.0.1'
            )
            
            # التحقق من الموثوقية
            is_whitelisted = IPSecurityManager.is_ip_whitelisted(
                user_id=test_user.id,
                ip_address='10.0.0.1'
            )
            
            assert is_whitelisted

    def test_non_whitelisted_ip(self, app, test_user):
        """اختبار عنوان IP غير موثوق"""
        with app.app_context():
            from security_services import IPSecurityManager
            
            is_whitelisted = IPSecurityManager.is_ip_whitelisted(
                user_id=test_user.id,
                ip_address='203.0.113.1'  # عنوان اختبار غير موثوق
            )
            
            assert not is_whitelisted


class TestSecurityLogging:
    """اختبارات سجل الأمان"""

    def test_action_logging(self, app, test_user):
        """اختبار تسجيل الإجراءات"""
        with app.app_context():
            from security_services import SecurityLog
            
            log = SecurityLog.log_action(
                user_id=test_user.id,
                action='password_change',
                resource_type='user',
                resource_id=test_user.id,
                status='success'
            )
            
            assert log.id is not None
            assert log.action == 'password_change'

    def test_log_retrieval(self, app, test_user):
        """اختبار استرجاع السجلات"""
        with app.app_context():
            from security_services import SecurityLog
            from models.security_enhanced import SecurityLog as SecurityLogModel
            
            # إنشاء عدة سجلات
            for i in range(5):
                SecurityLog.log_action(
                    user_id=test_user.id,
                    action='login',
                    status='success'
                )
            
            # استرجاع السجلات
            logs = SecurityLogModel.query.filter_by(
                user_id=test_user.id,
                action='login'
            ).all()
            
            assert len(logs) >= 5


class TestRateLimiting:
    """اختبارات تحديد معدل الطلبات"""

    def test_rate_limit_check(self, app):
        """اختبار فحص معدل الطلبات"""
        with app.app_context():
            from security_services import RateLimiter
            
            # محاكاة طلبات متعددة
            is_allowed, error = RateLimiter.check_rate_limit('/api/test')
            assert is_allowed

    def test_rate_limit_rule_creation(self, app):
        """اختبار إنشاء قاعدة معدل"""
        with app.app_context():
            from models.security_enhanced import RateLimitRule
            
            rule = RateLimitRule(
                endpoint='/api/test',
                method='POST',
                requests_per_minute=30,
                requests_per_hour=500
            )
            db.session.add(rule)
            db.session.commit()
            
            assert rule.id is not None


class TestSecurityUI:
    """اختبارات واجهات الأمان (اختياري - يتطلب Playwright)"""

    def test_password_policy_page_access(self, client, test_user):
        """اختبار الوصول إلى صفحة سياسة كلمات المرور"""
        with client:
            # محاكاة تسجيل الدخول
            response = client.get('/security/password-policy')
            
            # يجب إعادة توجيه إلى صفحة تسجيل الدخول بدون مصادقة
            assert response.status_code in [302, 401]


# اختبارات إضافية

class TestInputSanitization:
    """اختبارات تنظيف المدخلات"""

    def test_xss_protection(self, app):
        """اختبار الحماية من XSS"""
        with app.app_context():
            from security_middleware import InputSanitizer
            
            dangerous_input = '<script>alert("XSS")</script>Hello'
            sanitized = InputSanitizer.sanitize_input(dangerous_input)
            
            assert '<script>' not in sanitized
            assert 'alert' not in sanitized

    def test_sql_injection_detection(self, app):
        """اختبار كشف SQL Injection"""
        with app.app_context():
            from security_middleware import SQLInjectionProtection
            
            malicious_input = "admin'; DROP TABLE users; --"
            is_dangerous = SQLInjectionProtection.check_sql_injection(malicious_input)
            
            assert is_dangerous

    def test_safe_input(self, app):
        """اختبار المدخلات الآمنة"""
        with app.app_context():
            from security_middleware import SQLInjectionProtection
            
            safe_input = "John Smith"
            is_dangerous = SQLInjectionProtection.check_sql_injection(safe_input)
            
            assert not is_dangerous


if __name__ == '__main__':
    pytest.main([__file__, '-v'])