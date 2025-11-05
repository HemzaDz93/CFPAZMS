# -*- coding: utf-8 -*-
"""
نظام إدارة مراكز التكوين المهني (Multi-Tenant Management)
Vocational Centers Management Routes
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from sqlalchemy import and_, or_
from models import (
    db, VocationalCenter, User, UserRole, UserPermission,
    ActivityLog, Item, Recipe, MealRecord, 
    Transaction, Supplier, PurchaseOrder, AssetRegistration
)
from datetime import datetime
import uuid

# إنشاء Blueprint
vc_bp = Blueprint('vocational_centers', __name__, url_prefix='/vocational-centers')

# ==================== Middleware & Helpers ====================

def check_founder_access():
    """التحقق من أن المستخدم مؤسس"""
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول أولاً', 'danger')
        return False
    if current_user.role != UserRole.FOUNDER and current_user.role != UserRole.ADMIN:
        flash('صلاحية محدودة: هذا الخيار للمؤسسين فقط', 'danger')
        return False
    return True

def check_center_manager_access(center_id):
    """التحقق من أن المستخدم مدير المركز"""
    if not current_user.is_authenticated:
        return False
    
    # المؤسس يمكنه الوصول لأي مركز
    if current_user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
        return True
    
    # مدير المركز يمكنه الوصول لمركزه فقط
    if current_user.role == UserRole.CENTER_MANAGER:
        return current_user.center_id == center_id
    
    return False

def log_activity(action, entity_type, entity_id, old_value=None, new_value=None, center_id=None):
    """تسجيل النشاط"""
    try:
        activity = ActivityLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            center_id=center_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error logging activity: {str(e)}")

# ==================== Routes ====================

@vc_bp.route('/', methods=['GET'])
@login_required
def list_centers():
    """عرض قائمة المؤسسات"""
    
    # المؤسس يرى جميع المؤسسات
    if current_user.role in [UserRole.FOUNDER, UserRole.ADMIN]:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        centers = VocationalCenter.query.filter_by(
            is_active=True
        ).paginate(page=page, per_page=per_page)
        
        return render_template('vocational_centers/list.html', centers=centers)
    
    # مدير المركز يرى مركزه فقط
    elif current_user.role == UserRole.CENTER_MANAGER:
        if current_user.center_id:
            center = VocationalCenter.query.get(current_user.center_id)
            if center:
                return render_template('vocational_centers/detail.html', center=center)
        
        flash('لم يتم تعيين مركز لحسابك', 'warning')
        return redirect(url_for('dashboard.index'))
    
    else:
        flash('صلاحية محدودة', 'danger')
        return redirect(url_for('dashboard.index'))

@vc_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_center():
    """إضافة مركز تكوين جديد"""
    
    if not check_founder_access():
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            # التحقق من البيانات المطلوبة
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip()
            
            if not name or not code:
                flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
                return redirect(url_for('vocational_centers.add_center'))
            
            # التحقق من عدم تكرار الرمز
            if VocationalCenter.query.filter_by(code=code).first():
                flash('رمز المركز موجود بالفعل', 'danger')
                return redirect(url_for('vocational_centers.add_center'))
            
            # إنشاء المركز الجديد
            center = VocationalCenter(
                name=name,
                name_en=request.form.get('name_en', '').strip(),
                code=code,
                address=request.form.get('address', '').strip(),
                phone=request.form.get('phone', '').strip(),
                email=request.form.get('email', '').strip(),
                director_name=request.form.get('director_name', '').strip(),
                tax_id=request.form.get('tax_id', '').strip(),
                registration_number=request.form.get('registration_number', '').strip(),
                meal_cost_per_unit=float(request.form.get('meal_cost_per_unit', 2.5)),
                meal_alert_threshold=float(request.form.get('meal_alert_threshold', 500.0)),
                notes=request.form.get('notes', '').strip(),
                created_by_id=current_user.id
            )
            
            db.session.add(center)
            db.session.commit()
            
            # تسجيل النشاط
            log_activity(
                action='create',
                entity_type='VocationalCenter',
                entity_id=center.id,
                new_value=f"تم إنشاء المركز: {name}",
                center_id=center.id
            )
            
            flash(f'تم إنشاء المركز "{name}" بنجاح', 'success')
            return redirect(url_for('vocational_centers.list_centers'))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating center: {str(e)}")
            flash(f'خطأ عند إنشاء المركز: {str(e)}', 'danger')
            return redirect(url_for('vocational_centers.add_center'))
    
    return render_template('vocational_centers/add.html')

@vc_bp.route('/<center_id>', methods=['GET'])
@login_required
def view_center(center_id):
    """عرض تفاصيل المركز"""
    
    center = VocationalCenter.query.get(center_id)
    if not center:
        flash('المركز غير موجود', 'danger')
        return redirect(url_for('vocational_centers.list_centers'))
    
    # التحقق من الوصول
    if not check_center_manager_access(center_id):
        flash('لا توجد صلاحية للوصول لهذا المركز', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # احصائيات المركز
    stats = {
        'employees': User.query.filter_by(center_id=center_id, is_active=True).count(),
        'inventory_items': Item.query.filter_by(center_id=center_id, is_active=True).count(),
        'suppliers': Supplier.query.filter_by(center_id=center_id, is_active=True).count(),
        'recipes': Recipe.query.filter_by(center_id=center_id, is_active=True).count(),
        'recent_activity': ActivityLog.query.filter_by(center_id=center_id).order_by(
            ActivityLog.created_at.desc()
        ).limit(10).all()
    }
    
    return render_template('vocational_centers/detail.html', center=center, stats=stats)

@vc_bp.route('/<center_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_center(center_id):
    """تعديل بيانات المركز"""
    
    center = VocationalCenter.query.get(center_id)
    if not center:
        flash('المركز غير موجود', 'danger')
        return redirect(url_for('vocational_centers.list_centers'))
    
    if not check_center_manager_access(center_id):
        flash('لا توجد صلاحية للوصول لهذا المركز', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            # تخزين القيم القديمة
            old_data = {
                'name': center.name,
                'address': center.address,
                'phone': center.phone,
                'email': center.email
            }
            
            # تحديث البيانات
            center.name = request.form.get('name', center.name).strip()
            center.name_en = request.form.get('name_en', '').strip()
            center.address = request.form.get('address', '').strip()
            center.phone = request.form.get('phone', '').strip()
            center.email = request.form.get('email', '').strip()
            center.director_name = request.form.get('director_name', '').strip()
            center.tax_id = request.form.get('tax_id', '').strip()
            center.registration_number = request.form.get('registration_number', '').strip()
            center.meal_cost_per_unit = float(request.form.get('meal_cost_per_unit', center.meal_cost_per_unit))
            center.meal_alert_threshold = float(request.form.get('meal_alert_threshold', center.meal_alert_threshold))
            center.notes = request.form.get('notes', '').strip()
            
            db.session.commit()
            
            # تسجيل النشاط
            log_activity(
                action='update',
                entity_type='VocationalCenter',
                entity_id=center.id,
                old_value=str(old_data),
                new_value=f"تم تعديل المركز: {center.name}",
                center_id=center_id
            )
            
            flash('تم تحديث بيانات المركز بنجاح', 'success')
            return redirect(url_for('vocational_centers.view_center', center_id=center_id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating center: {str(e)}")
            flash(f'خطأ عند تحديث المركز: {str(e)}', 'danger')
    
    return render_template('vocational_centers/edit.html', center=center)

@vc_bp.route('/<center_id>/delete', methods=['POST'])
@login_required
def delete_center(center_id):
    """حذف المركز"""
    
    if not check_founder_access():
        return jsonify({'success': False, 'message': 'صلاحية محدودة'}), 403
    
    center = VocationalCenter.query.get(center_id)
    if not center:
        return jsonify({'success': False, 'message': 'المركز غير موجود'}), 404
    
    try:
        # التحقق من عدم وجود بيانات تابعة للمركز
        has_employees = User.query.filter_by(center_id=center_id).first()
        has_items = Item.query.filter_by(center_id=center_id).first()
        
        if has_employees or has_items:
            return jsonify({
                'success': False,
                'message': 'لا يمكن حذف المركز لأنه يحتوي على بيانات'
            }), 400
        
        # حذف المركز
        db.session.delete(center)
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(
            action='delete',
            entity_type='VocationalCenter',
            entity_id=center_id,
            new_value=f"تم حذف المركز: {center.name}",
            center_id=center_id
        )
        
        return jsonify({'success': True, 'message': 'تم حذف المركز بنجاح'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting center: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== Center Employees Management ====================

@vc_bp.route('/<center_id>/employees', methods=['GET'])
@login_required
def manage_employees(center_id):
    """إدارة موظفي المركز"""
    
    center = VocationalCenter.query.get(center_id)
    if not center:
        flash('المركز غير موجود', 'danger')
        return redirect(url_for('vocational_centers.list_centers'))
    
    if not check_center_manager_access(center_id):
        flash('لا توجد صلاحية للوصول لهذا المركز', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    employees = User.query.filter_by(
        center_id=center_id,
        is_active=True
    ).paginate(page=page, per_page=per_page)
    
    return render_template('vocational_centers/employees.html', center=center, employees=employees)

@vc_bp.route('/<center_id>/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee(center_id):
    """إضافة موظف للمركز"""
    
    center = VocationalCenter.query.get(center_id)
    if not center:
        flash('المركز غير موجود', 'danger')
        return redirect(url_for('vocational_centers.list_centers'))
    
    if not check_center_manager_access(center_id):
        flash('لا توجد صلاحية للوصول لهذا المركز', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            
            # التحقق من عدم تكرار اسم المستخدم أو البريد
            if User.query.filter_by(username=username).first():
                flash('اسم المستخدم مستخدم بالفعل', 'danger')
                return redirect(url_for('vocational_centers.add_employee', center_id=center_id))
            
            if User.query.filter_by(email=email).first():
                flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
                return redirect(url_for('vocational_centers.add_employee', center_id=center_id))
            
            # إنشاء المستخدم الجديد
            user = User(
                username=username,
                email=email,
                first_name=request.form.get('first_name', '').strip(),
                last_name=request.form.get('last_name', '').strip(),
                center_id=center_id,
                role=request.form.get('role', UserRole.WORKER),
                department=request.form.get('department', '').strip(),
                position=request.form.get('position', '').strip(),
                phone=request.form.get('phone', '').strip()
            )
            
            password = request.form.get('password', '')
            if password:
                user.set_password(password)
            else:
                user.set_password('12345678')  # Password افتراضي
            
            db.session.add(user)
            db.session.commit()
            
            # تسجيل النشاط
            log_activity(
                action='create',
                entity_type='User',
                entity_id=user.id,
                new_value=f"تم إنشاء موظف جديد: {user.full_name}",
                center_id=center_id
            )
            
            flash(f'تم إضافة الموظف "{user.full_name}" بنجاح', 'success')
            return redirect(url_for('vocational_centers.manage_employees', center_id=center_id))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding employee: {str(e)}")
            flash(f'خطأ عند إضافة الموظف: {str(e)}', 'danger')
    
    return render_template('vocational_centers/add_employee.html', center=center)

# ==================== Center Statistics ====================

@vc_bp.route('/<center_id>/statistics')
@login_required
def center_statistics(center_id):
    """إحصائيات المركز"""
    
    center = VocationalCenter.query.get(center_id)
    if not center:
        flash('المركز غير موجود', 'danger')
        return redirect(url_for('vocational_centers.list_centers'))
    
    if not check_center_manager_access(center_id):
        flash('لا توجد صلاحية للوصول لهذا المركز', 'danger')
        return redirect(url_for('dashboard.index'))
    
    stats = {
        'total_employees': User.query.filter_by(center_id=center_id, is_active=True).count(),
        'inventory_items': Item.query.filter_by(center_id=center_id, is_active=True).count(),
        'suppliers': Supplier.query.filter_by(center_id=center_id, is_active=True).count(),
        'recipes': Recipe.query.filter_by(center_id=center_id, is_active=True).count(),
        'total_transactions': Transaction.query.filter_by(center_id=center_id).count(),
        'recent_transactions': Transaction.query.filter_by(center_id=center_id).order_by(
            Transaction.created_at.desc()
        ).limit(5).all()
    }
    
    return render_template('vocational_centers/statistics.html', center=center, stats=stats)