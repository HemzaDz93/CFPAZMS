"""
نموذج الأمان المحسّن - المرحلة 2
Enhanced Security Model - Phase 2
"""

from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import ARRAY, JSON
import secrets
import hashlib
from cryptography.fernet import Fernet
import os
import sys
import importlib.util

# Import db from parent models.py
spec = importlib.util.spec_from_file_location("models_core", 
        os.path.join(os.path.dirname(__file__), '..', 'models.py'))
models_core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models_core)
db = models_core.db

class PasswordPolicy(db.Model):
    """سياسة كلمات المرور"""
    __tablename__ = 'password_policies'
    
    id = db.Column(db.Integer, primary_key=True)
    min_length = db.Column(db.Integer, default=12)
    require_uppercase = db.Column(db.Boolean, default=True)
    require_lowercase = db.Column(db.Boolean, default=True)
    require_numbers = db.Column(db.Integer, default=1)
    require_special_chars = db.Column(db.Integer, default=1)
    expiry_days = db.Column(db.Integer, default=90)
    history_count = db.Column(db.Integer, default=5)  # منع إعادة استخدام آخر 5 كلمات
    lockout_threshold = db.Column(db.Integer, default=5)
    lockout_duration_minutes = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PasswordPolicy min_length={self.min_length}>'


class PasswordHistory(db.Model):
    """سجل كلمات المرور السابقة"""
    __tablename__ = 'password_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.String(255), nullable=True)  # IP address or admin
    
    user = db.relationship('User', backref='password_history')
    
    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} changed_at={self.changed_at}>'


class SessionToken(db.Model):
    """إدارة رموز الجلسات"""
    __tablename__ = 'session_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    token_hash = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255), nullable=False)
    device_fingerprint = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref='session_tokens')
    
    def is_valid(self):
        """التحقق من صحة الرمز"""
        return (
            self.is_active and
            self.expires_at > datetime.utcnow() and
            self.revoked_at is None
        )
    
    def __repr__(self):
        return f'<SessionToken user_id={self.user_id} expires_at={self.expires_at}>'


class SecurityAlert(db.Model):
    """تنبيهات الأمان"""
    __tablename__ = 'security_alerts'
    
    ALERT_TYPES = {
        'failed_login': 'محاولة دخول فاشلة',
        'account_lockout': 'قفل الحساب',
        'password_change': 'تغيير كلمة المرور',
        'permission_denied': 'حق الوصول مرفوض',
        'data_access': 'الوصول إلى البيانات',
        'unusual_activity': 'نشاط غير عادي',
        'ip_change': 'تغيير عنوان IP',
        'suspicious_login': 'دخول مريب',
        'privilege_escalation': 'محاولة رفع الصلاحيات',
        'data_export': 'تصدير البيانات',
    }
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default='low')  # low, medium, high, critical
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    alert_metadata = db.Column(JSON, nullable=True)
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='security_alerts')
    acknowledged_user = db.relationship('User', foreign_keys=[acknowledged_by])
    
    def __repr__(self):
        return f'<SecurityAlert type={self.alert_type} severity={self.severity}>'


class IPWhitelist(db.Model):
    """قائمة عناوين IP الموثوقة"""
    __tablename__ = 'ip_whitelist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    device_name = db.Column(db.String(255), nullable=True)
    device_fingerprint = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref='whitelisted_ips')
    
    def is_valid(self):
        """التحقق من صحة عنوان IP الموثوق"""
        return (
            self.is_active and
            (self.expires_at is None or self.expires_at > datetime.utcnow())
        )
    
    def __repr__(self):
        return f'<IPWhitelist user_id={self.user_id} ip={self.ip_address}>'


class AccessKey(db.Model):
    """مفاتيح الوصول الشخصية (API Keys)"""
    __tablename__ = 'access_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_name = db.Column(db.String(255), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)
    key_prefix = db.Column(db.String(20), nullable=False)  # آخر 20 حرف من المفتاح
    permissions = db.Column(JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    created_by_ip = db.Column(db.String(45), nullable=True)
    
    user = db.relationship('User', backref='access_keys')
    
    def is_valid(self):
        """التحقق من صحة مفتاح الوصول"""
        return (
            self.is_active and
            self.revoked_at is None and
            (self.expires_at is None or self.expires_at > datetime.utcnow())
        )
    
    @staticmethod
    def generate_key():
        """توليد مفتاح وصول جديد"""
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[-20:]
        return key, key_hash, key_prefix
    
    def __repr__(self):
        return f'<AccessKey key_name={self.key_name} prefix={self.key_prefix}>'


class SecurityLog(db.Model):
    """سجل الأمان التفصيلي"""
    __tablename__ = 'security_logs'
    
    LOG_ACTIONS = {
        'login': 'دخول',
        'logout': 'خروج',
        'password_change': 'تغيير كلمة المرور',
        'mfa_setup': 'إعداد 2FA',
        'mfa_disable': 'تعطيل 2FA',
        'key_generated': 'توليد مفتاح',
        'key_revoked': 'إلغاء مفتاح',
        'permission_granted': 'منح صلاحية',
        'permission_revoked': 'إلغاء صلاحية',
        'data_accessed': 'الوصول للبيانات',
        'data_modified': 'تعديل البيانات',
        'data_deleted': 'حذف البيانات',
        'export_action': 'تصدير',
        'import_action': 'استيراد',
    }
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    old_values = db.Column(JSON, nullable=True)
    new_values = db.Column(JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='success')  # success, failed
    error_message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='security_logs')
    
    def __repr__(self):
        return f'<SecurityLog action={self.action} timestamp={self.timestamp}>'


class DataEncryption(db.Model):
    """إدارة مفاتيح التشفير"""
    __tablename__ = 'data_encryption'
    
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(255), nullable=False)
    encryption_key = db.Column(db.String(255), nullable=False)
    algorithm = db.Column(db.String(50), default='Fernet')
    key_rotation_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def generate_encryption_key():
        """توليد مفتاح تشفير جديد"""
        return Fernet.generate_key().decode()
    
    def __repr__(self):
        return f'<DataEncryption field_name={self.field_name}>'


class ComplianceRecord(db.Model):
    """سجلات الامتثال"""
    __tablename__ = 'compliance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    compliance_type = db.Column(db.String(100), nullable=False)  # GDPR, SOC2, ISO27001, etc.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    evidence = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref='compliance_records')
    
    def __repr__(self):
        return f'<ComplianceRecord type={self.compliance_type}>'


class RateLimitRule(db.Model):
    """قواعد تحديد معدل الطلبات"""
    __tablename__ = 'rate_limit_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)  # GET, POST, etc.
    requests_per_minute = db.Column(db.Integer, default=60)
    requests_per_hour = db.Column(db.Integer, default=1000)
    bypass_roles = db.Column(ARRAY(db.String), default=[])  # الأدوار التي تتجاوز القيود
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RateLimitRule endpoint={self.endpoint}>'


class RateLimitViolation(db.Model):
    """انتهاكات تحديد معدل الطلبات"""
    __tablename__ = 'rate_limit_violations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    request_count = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action_taken = db.Column(db.String(50), nullable=True)  # blocked, logged, etc.
    
    user = db.relationship('User', backref='rate_limit_violations')
    
    def __repr__(self):
        return f'<RateLimitViolation ip={self.ip_address} endpoint={self.endpoint}>'