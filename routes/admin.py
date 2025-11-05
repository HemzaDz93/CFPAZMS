from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, current_app
)
from flask_login import login_required, current_user
from models import (
    db, User, UserRole, OrganizationSettings, 
    UserPermission, ActivityLog
)
from permissions_config import get_permissions_by_category, get_all_permissions_flat
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==================== Organization Settings ====================

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def organization_settings():
    """إعدادات المؤسسة"""
    if not current_user.has_granular_permission('admin_manage_organization_settings'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    org_settings = OrganizationSettings.query.first()
    if not org_settings:
        org_settings = OrganizationSettings()
        db.session.add(org_settings)
        db.session.commit()
    
    if request.method == 'POST':
        old_ministry = org_settings.ministry_name
        old_directorate = org_settings.directorate_name
        old_institution = org_settings.institution_name
        
        org_settings.ministry_name = request.form.get('ministry_name', org_settings.ministry_name)
        org_settings.ministry_name_en = request.form.get('ministry_name_en', '')
        
        org_settings.directorate_name = request.form.get('directorate_name', org_settings.directorate_name)
        org_settings.directorate_name_en = request.form.get('directorate_name_en', '')
        
        org_settings.institution_name = request.form.get('institution_name', org_settings.institution_name)
        org_settings.institution_name_en = request.form.get('institution_name_en', '')
        
        org_settings.institution_code = request.form.get('institution_code', org_settings.institution_code)
        org_settings.address = request.form.get('address', org_settings.address)
        org_settings.phone = request.form.get('phone', org_settings.phone)
        org_settings.email = request.form.get('email', org_settings.email)
        org_settings.tax_id = request.form.get('tax_id', org_settings.tax_id)
        org_settings.website = request.form.get('website', org_settings.website)
        
        # Restaurant Settings
        try:
            meal_cost = request.form.get('meal_cost_per_unit')
            if meal_cost:
                org_settings.meal_cost_per_unit = float(meal_cost)
        except (ValueError, TypeError):
            pass  # إبقاء القيمة الحالية إذا كانت القيمة غير صحيحة
        
        try:
            alert_threshold = request.form.get('meal_alert_threshold')
            if alert_threshold:
                org_settings.meal_alert_threshold = float(alert_threshold)
        except (ValueError, TypeError):
            pass  # إبقاء القيمة الحالية إذا كانت القيمة غير صحيحة
        
        org_settings.updated_by = current_user.full_name
        
        db.session.commit()
        
        # تسجيل النشاط
        activity_log = ActivityLog(
            user_id=current_user.id,
            action="تحديث إعدادات المؤسسة",
            entity_type='OrganizationSettings',
            entity_id=str(org_settings.id),
            old_value=f"{old_ministry} / {old_directorate} / {old_institution}",
            new_value=f"{org_settings.ministry_name} / {org_settings.directorate_name} / {org_settings.institution_name}"
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تحديث إعدادات المؤسسة بنجاح', 'success')
        return redirect(url_for('admin.organization_settings'))
    
    return render_template('admin/organization_settings.html', org_settings=org_settings)

# ==================== Users Management ====================

@admin_bp.route('/users')
@login_required
def users():
    """إدارة المستخدمين"""
    if not current_user.has_granular_permission('admin_view_users'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    if role:
        query = query.filter_by(role=role)
    
    users = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    
    return render_template(
        'admin/users.html',
        users=users,
        search=search,
        selected_role=role
    )

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """إضافة مستخدم جديد"""
    if not current_user.has_granular_permission('admin_add_user'):
        flash('ليس لديك صلاحية للقيام بهذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # التحقق من البيانات
        if not all([username, email, first_name, last_name, password]):
            flash('جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('admin.add_user'))
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'warning')
            return redirect(url_for('admin.add_user'))
        
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('admin.add_user'))
        
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني موجود بالفعل', 'danger')
            return redirect(url_for('admin.add_user'))
        
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=request.form.get('role', UserRole.WORKER),
            department=request.form.get('department', ''),
            position=request.form.get('position', ''),
            rank=request.form.get('rank', ''),
            phone=request.form.get('phone', ''),
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # للحصول على user_id قبل الـ commit
        
        # إضافة الصلاحيات المختارة
        _update_user_permissions(user.id, request.form)
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"إضافة مستخدم جديد: {username}",
            entity_type='User',
            entity_id=user.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash(f'تم إضافة المستخدم {user.full_name} بنجاح', 'success')
        return redirect(url_for('admin.users'))
    
    roles = [(role.value, role.value) for role in UserRole]
    permissions = get_permissions_by_category()
    return render_template('admin/add_user.html', roles=roles, permissions=permissions)

@admin_bp.route('/users/edit/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """تعديل بيانات مستخدم"""
    if not current_user.has_granular_permission('admin_edit_user'):
        flash('ليس لديك صلاحية للقيام بهذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        old_role = user.role
        
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.email = request.form.get('email', user.email)
        user.role = request.form.get('role', user.role)
        user.department = request.form.get('department', user.department)
        user.position = request.form.get('position', user.position)
        user.rank = request.form.get('rank', user.rank)
        user.phone = request.form.get('phone', user.phone)
        user.address = request.form.get('address', user.address)
        user.is_active = request.form.get('is_active') == 'on'
        
        # تحديث الصلاحيات المختارة
        _update_user_permissions(user.id, request.form)
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"تعديل مستخدم: {user.username}",
            entity_type='User',
            entity_id=user.id,
            old_value=old_role,
            new_value=user.role
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تحديث بيانات المستخدم بنجاح', 'success')
        return redirect(url_for('admin.users'))
    
    roles = [(role.value, role.value) for role in UserRole]
    permissions = get_permissions_by_category()
    user_permissions = get_all_permissions_flat()
    user_allowed_perms = user.get_all_permissions()
    
    return render_template('admin/edit_user.html', user=user, roles=roles, 
                          permissions=permissions, user_allowed_perms=user_allowed_perms,
                          user_permissions=user_permissions)

@admin_bp.route('/activity-logs')
@login_required
def activity_logs():
    """سجل النشاطات"""
    if not current_user.has_granular_permission('admin_view_activity_logs'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', '')
    entity_type = request.args.get('entity_type', '')
    
    query = ActivityLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    logs = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE']
    )
    
    return render_template('admin/activity_logs.html', logs=logs)


# ==================== Helper Functions ====================

def _update_user_permissions(user_id, form_data):
    """تحديث صلاحيات المستخدم من بيانات النموذج"""
    all_perms = get_all_permissions_flat()
    
    # حذف جميع الصلاحيات الحالية
    UserPermission.query.filter_by(user_id=user_id).delete()
    
    # إضافة الصلاحيات الجديدة
    for perm_key, perm_info in all_perms.items():
        # التحقق من وجود checkbox للصلاحية
        is_allowed = form_data.get(f'perm_{perm_key}') == 'on'
        
        permission = UserPermission(
            user_id=user_id,
            permission_key=perm_key,
            permission_name=perm_info['name'],
            permission_category=perm_info['category'],
            is_allowed=is_allowed
        )
        db.session.add(permission)
    
    db.session.commit()