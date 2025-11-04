from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def require_granular_permission(permission_key):
    """Decorator to enforce granular permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_granular_permission(permission_key):
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator