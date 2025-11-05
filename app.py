from flask import Flask, render_template, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, current_user, login_required
from config import config
from models import db, User, OrganizationSettings, UserRole, Notification
from permissions_config import get_all_permissions_flat
import os
import click
from datetime import datetime, timedelta
import base64

def create_app(config_name=None):
    """مصنع التطبيق"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = config.get(config_name, config['default'])
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # تهيئة قاعدة البيانات
    db.init_app(app)
    
    # تهيئة نظام الأمان المتقدم (Phase 2)
    try:
        from security_middleware import init_security_middleware
        init_security_middleware(app)
    except ImportError:
        app.logger.warning('Security middleware not available')
    
    # تهيئة نظام Multi-Tenant (عزل البيانات حسب المركز)
    try:
        from multi_tenant_middleware import init_multi_tenant_middleware
        init_multi_tenant_middleware(app)
    except ImportError:
        app.logger.warning('Multi-tenant middleware not available')
    
    # تهيئة نظام تسجيل الدخول
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # تسجيل Blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.dashboard import dashboard_bp
    from routes.inventory import inventory_bp
    from routes.suppliers import suppliers_bp
    from routes.equipment import equipment_bp
    from routes.restaurant import restaurant_bp
    from routes.restaurant_advanced import restaurant_advanced_bp
    from routes.reports import reports_bp
    from routes.employee_requests import employee_requests_bp
    from routes.about import about_bp
    from routes.notifications import notifications_bp
    from routes.employee_meals import employee_meals_bp
    from routes.security_advanced import security_bp
    from routes.vocational_centers import vc_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(restaurant_advanced_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(employee_requests_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(employee_meals_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(vc_bp)
    
    # Jinja2 Filters
    @app.template_filter('b64encode')
    def b64encode_filter(data):
        """Encode binary data to base64 string for templates"""
        if isinstance(data, bytes):
            return base64.b64encode(data).decode('utf-8')
        return data
    
    # Context processor
    @app.context_processor
    def inject_org_settings():
        """إدراج إعدادات المؤسسة في جميع القوالب"""
        org_settings = OrganizationSettings.query.first()
        if not org_settings:
            org_settings = OrganizationSettings()
        
        def has_permission(permission_key):
            """دالة للتحقق من الصلاحيات في القوالب"""
            if not current_user.is_authenticated:
                return False
            return current_user.has_granular_permission(permission_key)
        
        return {
            'org_settings': org_settings,
            'current_year': datetime.now().year,
            'current_user': current_user,
            'has_permission': has_permission,
            'utcnow': datetime.utcnow,
            'now': datetime.utcnow,
        }
    
    @app.before_request
    def before_request():
        """قبل كل طلب"""
        if current_user.is_authenticated:
            session.permanent = True
            app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']
    
    # Errorhandlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Routes
    @app.route('/')
    def index():
        """الصفحة الرئيسية"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    # API Routes
    @app.route('/api/notifications', methods=['GET'])
    @login_required
    def api_get_notifications():
        """واجهة API لجلب الإشعارات (للاستخدام من الجانب الأمامي)"""
        # جلب الإشعارات الجديدة (آخر 10)
        notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        # حساب عدد الإشعارات غير المقروءة
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()
        
        # تنسيق الإشعارات
        formatted_notifications = []
        for notif in notifications:
            # حساب الوقت المنقضي
            time_delta = datetime.utcnow() - notif.created_at
            if time_delta.days > 0:
                time_ago = f"منذ {time_delta.days} يوم{'ا' if time_delta.days > 1 else ''}"
            elif time_delta.seconds > 3600:
                hours = time_delta.seconds // 3600
                time_ago = f"منذ {hours} ساعة{'ت' if hours > 1 else ''}"
            elif time_delta.seconds > 60:
                minutes = time_delta.seconds // 60
                time_ago = f"منذ {minutes} دقيقة"
            else:
                time_ago = "للتو"
            
            formatted_notifications.append({
                'id': str(notif.id),
                'title': notif.title or 'إشعار جديد',
                'message': notif.message or '',
                'type': notif.notification_type or 'info',
                'is_unread': not notif.is_read,
                'time_ago': time_ago,
                'created_at': notif.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'unread_count': unread_count,
            'notifications': formatted_notifications,
            'total_count': Notification.query.filter_by(user_id=current_user.id).count()
        })
    
    # CLI Commands
    @app.cli.command()
    def init_db():
        """تهيئة قاعدة البيانات"""
        db.create_all()
        
        # إنشاء إعدادات المؤسسة الافتراضية
        if not OrganizationSettings.query.first():
            org = OrganizationSettings(
                ministry_name="الوزارة ",
                directorate_name="المديرية ",
                institution_name="المؤسسة ",
                institution_code="INST001",
                address="العنوان",
                phone="+213555555555",
                email="info@institution.dz",
                tax_id="123456789"
            )
            db.session.add(org)
            db.session.commit()
            print("تم إنشاء إعدادات المؤسسة بنجاح")
        
        # إنشاء مدير النظام
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='benselilih.messaoud@gmail.com',
                first_name='بن سليليح',
                last_name='المسعود',
                role=UserRole.ADMIN,
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("تم إنشاء حساب المدير بنجاح - اسم المستخدم: admin - كلمة المرور: admin123")
        
        print("تم تهيئة قاعدة البيانات بنجاح")
    
    @app.cli.command()
    def drop_db():
        """حذف قاعدة البيانات"""
        if click.confirm('هل أنت متأكد من حذف جميع البيانات؟'):
            db.drop_all()
            print("تم حذف قاعدة البيانات")
    
    return app

if __name__ == '__main__':
    import click
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5002)