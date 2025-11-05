import os
from datetime import timedelta

class Config:
    """إعدادات التطبيق الأساسية"""
    
    # Flask Configuration
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///cfpa_zms.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    
    # Date Format
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Application Settings
    ITEMS_PER_PAGE = 20
    ALLOW_REGISTRATION = False  # Admin only can create users
    
    # Employee Meals Settings
    MEAL_COST_PER_UNIT = float(os.environ.get('MEAL_COST_PER_UNIT', 2.5))  # دينار جزائري
    MEAL_ALERT_THRESHOLD = float(os.environ.get('MEAL_ALERT_THRESHOLD', 500))  # التنبيه عند تجاوز 500 دج
    
    # Advanced Security Settings - Phase 2
    # Password Policy
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 12))
    PASSWORD_REQUIRE_UPPERCASE = os.environ.get('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_LOWERCASE = os.environ.get('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_NUMBERS = int(os.environ.get('PASSWORD_REQUIRE_NUMBERS', 1))
    PASSWORD_REQUIRE_SPECIAL_CHARS = int(os.environ.get('PASSWORD_REQUIRE_SPECIAL_CHARS', 1))
    PASSWORD_EXPIRY_DAYS = int(os.environ.get('PASSWORD_EXPIRY_DAYS', 90))
    PASSWORD_HISTORY_COUNT = int(os.environ.get('PASSWORD_HISTORY_COUNT', 5))
    
    # Session Management
    SESSION_TIMEOUT_MINUTES = int(os.environ.get('SESSION_TIMEOUT_MINUTES', 30))
    MAX_SESSIONS_PER_USER = int(os.environ.get('MAX_SESSIONS_PER_USER', 5))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_DEFAULT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_DEFAULT_PER_MINUTE', 60))
    
    # Login Security
    LOGIN_ATTEMPT_LIMIT = int(os.environ.get('LOGIN_ATTEMPT_LIMIT', 5))
    LOGIN_LOCKOUT_DURATION_MINUTES = int(os.environ.get('LOGIN_LOCKOUT_DURATION_MINUTES', 30))
    
    # MFA Settings
    MFA_ENABLED = os.environ.get('MFA_ENABLED', 'false').lower() == 'true'
    MFA_REQUIRED_FOR_ADMINS = os.environ.get('MFA_REQUIRED_FOR_ADMINS', 'true').lower() == 'true'
    
    # IP Whitelisting
    IP_WHITELIST_ENABLED = os.environ.get('IP_WHITELIST_ENABLED', 'false').lower() == 'true'
    
    # Encryption
    ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'true').lower() == 'true'
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')
    
    # OAuth Configuration (for SSO)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', '')
    AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', '')
    
    # Audit Logging
    AUDIT_LOGGING_ENABLED = os.environ.get('AUDIT_LOGGING_ENABLED', 'true').lower() == 'true'
    SECURITY_LOG_RETENTION_DAYS = int(os.environ.get('SECURITY_LOG_RETENTION_DAYS', 365))
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    @staticmethod
    def init_app(app):
        """تهيئة التطبيق"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """إعدادات التطوير"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """إعدادات الإنتاج"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """إعدادات الاختبار"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}