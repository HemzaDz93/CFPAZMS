"""
نماذج الأمان والتدقيق
"""

from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import ARRAY
from models import db

class UserMFA(db.Model):
    """نموذج المصادقة الثنائية للمستخدم"""
    __tablename__ = 'user_mfa'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    secret = db.Column(db.String(32), nullable=False)
    is_enabled = db.Column(db.Boolean, default=False)
    backup_codes = db.Column(ARRAY(db.String), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('mfa', uselist=False))

class AuditLog(db.Model):
    """نموذج سجل التدقيق"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    success = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')

class LoginAttempt(db.Model):
    """نموذج محاولات تسجيل الدخول"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='login_attempts')

class SecuritySettings(db.Model):
    """نموذج إعدادات الأمان العامة"""
    __tablename__ = 'security_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_setting(cls, key, default=None):
        """الحصول على قيمة إعداد"""
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default

    @classmethod
    def set_setting(cls, key, value, description=None):
        """تعيين قيمة إعداد"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            if description:
                setting.description = description
        else:
            setting = cls(
                setting_key=key,
                setting_value=value,
                description=description
            )
            db.session.add(setting)
        db.session.commit()

# تحديث نموذج المستخدم
def update_user_model(User):
    """إضافة علاقات وطرق الأمان لنموذج المستخدم"""
    
    User.login_attempts = db.relationship('LoginAttempt', back_populates='user')
    User.audit_logs = db.relationship('AuditLog', back_populates='user')
    User.mfa = db.relationship('UserMFA', back_populates='user', uselist=False)
    
    def has_mfa_enabled(self):
        """التحقق من تفعيل المصادقة الثنائية"""
        return bool(self.mfa and self.mfa.is_enabled)
    
    def get_failed_login_attempts(self, minutes=5):
        """الحصول على عدد محاولات تسجيل الدخول الفاشلة"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return LoginAttempt.query.filter(
            LoginAttempt.user_id == self.id,
            LoginAttempt.success == False,
            LoginAttempt.timestamp >= cutoff
        ).count()
    
    def is_locked_out(self):
        """التحقق من قفل الحساب"""
        max_attempts = int(SecuritySettings.get_setting('max_login_attempts', '5'))
        lockout_duration = int(SecuritySettings.get_setting('lockout_duration_minutes', '15'))
        
        return self.get_failed_login_attempts(lockout_duration) >= max_attempts
    
    User.has_mfa_enabled = has_mfa_enabled
    User.get_failed_login_attempts = get_failed_login_attempts
    User.is_locked_out = is_locked_out
    
    return User