# -*- coding: utf-8 -*-
"""
Multi-Tenant Middleware
نظام عزل البيانات حسب المركز (Multi-Tenant Isolation)
"""

from flask import current_app, request, abort, session
from flask_login import current_user
from models import User, UserRole, VocationalCenter
from functools import wraps

def get_user_centers():
    """الحصول على قائمة المراكز المسموحة للمستخدم الحالي"""
    
    if not current_user.is_authenticated:
        return []
    
    # المؤسس يمكنه الوصول لجميع المراكز
    if current_user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
        return VocationalCenter.query.filter_by(is_active=True).all()
    
    # موظفو المركز يمكنهم الوصول لمركزهم فقط
    if current_user.center_id:
        center = VocationalCenter.query.get(current_user.center_id)
        if center and center.is_active:
            return [center]
    
    return []

def get_current_center():
    """الحصول على المركز الحالي"""
    
    if not current_user.is_authenticated:
        return None
    
    # المؤسس قد لا يكون لديه مركز محدد
    if current_user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
        # محاولة الحصول على المركز من session أو request
        center_id = session.get('current_center_id') or request.args.get('center_id')
        if center_id:
            center = VocationalCenter.query.get(center_id)
            if center and center.is_active:
                return center
        return None
    
    # موظفو المركز لديهم مركز محدد
    if current_user.center_id:
        center = VocationalCenter.query.get(current_user.center_id)
        if center and center.is_active:
            return center
    
    return None

def require_center_access(center_id):
    """Decorator للتحقق من وصول المستخدم للمركز"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # المؤسس يمكنه الوصول لأي مركز
            if current_user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
                return f(*args, **kwargs)
            
            # موظفو المركز يمكنهم الوصول لمركزهم فقط
            if current_user.center_id == center_id:
                return f(*args, **kwargs)
            
            abort(403)
        return decorated_function
    return decorator

def filter_query_by_center(query, center_id, model):
    """
    تصفية الاستعلام حسب المركز
    
    Args:
        query: SQLAlchemy query object
        center_id: معرّف المركز أو None للمراكز المشتركة
        model: نموذج البيانات
    
    Returns:
        Filtered query
    """
    
    if center_id is None:
        return query
    
    # التحقق من وجود حقل center_id في النموذج
    if hasattr(model, 'center_id'):
        return query.filter_by(center_id=center_id)
    
    return query

def ensure_center_isolation():
    """
    Middleware لضمان عزل البيانات حسب المركز
    يتم تطبيقه قبل كل طلب
    """
    
    if not current_user.is_authenticated:
        return
    
    # تعيين المركز الحالي في session
    if current_user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
        center_id = request.args.get('center_id')
        if center_id:
            session['current_center_id'] = center_id
    else:
        # موظفو المركز لديهم مركز محدد
        session['current_center_id'] = current_user.center_id

def is_founder():
    """التحقق من أن المستخدم مؤسس"""
    return current_user.is_authenticated and current_user.role in [UserRole.FOUNDER, UserRole.ADMIN]

def is_center_manager():
    """التحقق من أن المستخدم مدير مركز"""
    return current_user.is_authenticated and current_user.role == UserRole.CENTER_MANAGER

def can_access_center(center_id):
    """التحقق من أن المستخدم يمكنه الوصول للمركز"""
    
    if not current_user.is_authenticated:
        return False
    
    # المؤسس يمكنه الوصول لأي مركز
    if current_user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
        return True
    
    # موظفو المركز يمكنهم الوصول لمركزهم فقط
    return current_user.center_id == center_id

# ==================== Query Builders for Multi-Tenant ====================

class MultiTenantQuery:
    """
    فئة لبناء استعلامات آمنة متعددة المستأجرين
    """
    
    @staticmethod
    def get_user_items(user=None):
        """الحصول على أصناف المستخدم"""
        from models import Item
        
        if user is None:
            user = current_user
        
        if not user.is_authenticated:
            return Item.query.filter_by(id=None)  # لا شيء
        
        if user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
            return Item.query
        
        if user.center_id:
            return Item.query.filter_by(center_id=user.center_id)
        
        return Item.query.filter_by(id=None)
    
    @staticmethod
    def get_user_suppliers(user=None):
        """الحصول على موردي المستخدم"""
        from models import Supplier
        
        if user is None:
            user = current_user
        
        if not user.is_authenticated:
            return Supplier.query.filter_by(id=None)
        
        if user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
            return Supplier.query
        
        if user.center_id:
            return Supplier.query.filter_by(center_id=user.center_id)
        
        return Supplier.query.filter_by(id=None)
    
    @staticmethod
    def get_user_recipes(user=None):
        """الحصول على وصفات المستخدم"""
        from models import Recipe
        
        if user is None:
            user = current_user
        
        if not user.is_authenticated:
            return Recipe.query.filter_by(id=None)
        
        if user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
            return Recipe.query
        
        if user.center_id:
            return Recipe.query.filter_by(center_id=user.center_id)
        
        return Recipe.query.filter_by(id=None)
    
    @staticmethod
    def get_user_transactions(user=None):
        """الحصول على عمليات المستخدم"""
        from models import Transaction
        
        if user is None:
            user = current_user
        
        if not user.is_authenticated:
            return Transaction.query.filter_by(id=None)
        
        if user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
            return Transaction.query
        
        if user.center_id:
            return Transaction.query.filter_by(center_id=user.center_id)
        
        return Transaction.query.filter_by(id=None)

def init_multi_tenant_middleware(app):
    """تهيئة Middleware متعدد المستأجرين"""
    
    @app.before_request
    def before_request_multi_tenant():
        """قبل كل طلب - ضمان عزل البيانات"""
        ensure_center_isolation()
    
    # إضافة الدوال المساعدة إلى template context
    @app.context_processor
    def inject_multi_tenant_helpers():
        return {
            'get_current_center': get_current_center,
            'get_user_centers': get_user_centers,
            'can_access_center': can_access_center,
            'is_founder': is_founder,
            'is_center_manager': is_center_manager
        }