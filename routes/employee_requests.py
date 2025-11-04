# -*- coding: utf-8 -*-
"""
مسارات طلبات الموظفين للمنتجات
Routes for Employee Stock Requests
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime as dt
from functools import wraps
import uuid

from models import (
    db, User, Item, ItemCategory_Model, StockRequest, StockRequestItem,
    Notification, ActivityLog, Transaction, TransactionType, UserRole
)
from auth_helpers import require_granular_permission

# إنشاء blueprint
employee_requests_bp = Blueprint('employee_requests', __name__, url_prefix='/employee-requests')


def can_approve_requests(f):
    """ديكوريتر للتحقق من صلاحية الموافقة على الطلبات"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # يمكن لأمين المخزن والمحاسب والمدير الموافقة
        allowed_roles = [UserRole.WAREHOUSE_MANAGER.value, 
                        UserRole.ACCOUNTANT.value, 
                        UserRole.DIRECTOR.value,
                        UserRole.ADMIN.value]
        
        if current_user.role not in allowed_roles:
            flash('ليس لديك صلاحية للموافقة على الطلبات', 'danger')
            return redirect(url_for('employee_requests.list_requests'))
        
        return f(*args, **kwargs)
    return decorated_function


def generate_request_number():
    """توليد رقم فريد للطلب"""
    prefix = dt.now().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4())[:8].upper()
    return f"REQ-{prefix}-{random_suffix}"


@employee_requests_bp.route('/', methods=['GET'])
@login_required
def list_requests():
    """عرض قائمة الطلبات - جميع الطلبات للمسؤولين أو طلبات الموظف الشخصية فقط"""
    # التحقق من الصلاحيات
    can_view_own = current_user.has_granular_permission('requests_view_own')
    can_view_all = current_user.has_granular_permission('requests_view_all')
    
    # إذا لم يكن لديه أي صلاحية عرض
    if not (can_view_own or can_view_all):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    
    # إذا كان له صلاحية عرض الكل، عرض جميع الطلبات، وإلا عرض طلبات الموظف فقط
    if can_view_all:
        query = StockRequest.query
    else:
        query = StockRequest.query.filter_by(requested_by_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # ترتيب حسب التاريخ الأحدث
    paginated = query.order_by(StockRequest.request_date.desc()).paginate(
        page=page, per_page=10
    )
    
    return render_template(
        'employee_requests/list.html',
        requests=paginated.items,
        pagination=paginated,
        status_filter=status_filter,
        can_view_all=can_view_all,
        can_approve=current_user.has_granular_permission('requests_approve'),
        can_create=current_user.has_granular_permission('requests_create')
    )


@employee_requests_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_request():
    """إنشاء طلب جديد"""
    # التحقق من صلاحية الإنشاء
    if not current_user.has_granular_permission('requests_create'):
        flash('ليس لديك صلاحية لإنشاء طلبات', 'danger')
        return redirect(url_for('employee_requests.list_requests'))
    
    if request.method == 'POST':
        try:
            # إنشاء طلب جديد
            new_request = StockRequest(
                request_number=generate_request_number(),
                requested_by_id=current_user.id,
                notes=request.form.get('notes', '')
            )
            
            db.session.add(new_request)
            db.session.flush()  # للحصول على ID
            
            # معالجة المنتجات المطلوبة
            items_data = request.form.getlist('item_id')
            quantities = request.form.getlist('quantity')
            
            if not items_data:
                flash('يجب اختيار منتج واحد على الأقل', 'warning')
                return redirect(url_for('employee_requests.create_request'))
            
            for item_id, qty in zip(items_data, quantities):
                if not qty or float(qty) <= 0:
                    continue
                
                item = Item.query.get(item_id)
                if not item:
                    continue
                
                request_item = StockRequestItem(
                    request_id=new_request.id,
                    item_id=item_id,
                    quantity=float(qty),
                    unit_price=item.unit_price,
                    notes=request.form.get(f'notes_{item_id}', '')
                )
                db.session.add(request_item)
            
            db.session.commit()
            
            # إنشاء إشعار للمسؤولين
            _send_request_notification(new_request)
            
            # تسجيل النشاط
            activity = ActivityLog(
                user_id=current_user.id,
                action='إنشاء طلب منتجات',
                entity_type='StockRequest',
                entity_id=new_request.id,
                new_value=f"الطلب رقم {new_request.request_number}"
            )
            db.session.add(activity)
            db.session.commit()
            
            flash(f'تم إنشاء الطلب بنجاح: {new_request.request_number}', 'success')
            return redirect(url_for('employee_requests.view_request', request_id=new_request.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إنشاء الطلب: {str(e)}', 'danger')
            return redirect(url_for('employee_requests.create_request'))
    
    # GET request - عرض نموذج الطلب
    categories = ItemCategory_Model.query.filter_by(is_active=True).all()
    items = Item.query.filter_by(is_active=True).all()
    
    return render_template(
        'employee_requests/add.html',
        categories=categories,
        items=items
    )


@employee_requests_bp.route('/<request_id>', methods=['GET'])
@login_required
def view_request(request_id):
    """عرض تفاصيل الطلب"""
    stock_request = StockRequest.query.get_or_404(request_id)
    
    # التحقق من الصلاحيات
    is_owner = stock_request.requested_by_id == current_user.id
    can_view_all = current_user.has_granular_permission('requests_view_all')
    can_view_own = current_user.has_granular_permission('requests_view_own')
    
    # التحقق من أن الموظف يرى طلبه أو أن له صلاحية عرض الكل
    if not ((is_owner and can_view_own) or can_view_all):
        flash('ليس لديك صلاحية لعرض هذا الطلب', 'danger')
        return redirect(url_for('employee_requests.list_requests'))
    
    can_approve = current_user.has_granular_permission('requests_approve')
    
    return render_template(
        'employee_requests/view.html',
        request=stock_request,
        is_owner=is_owner,
        is_approver=can_approve
    )


@employee_requests_bp.route('/admin/pending', methods=['GET'])
@login_required
def admin_pending_requests():
    """عرض الطلبات المعلقة للمسؤول"""
    # التحقق من صلاحية الموافقة على الطلبات
    if not current_user.has_granular_permission('requests_approve'):
        flash('ليس لديك صلاحية الموافقة على الطلبات', 'danger')
        return redirect(url_for('employee_requests.list_requests'))
    
    page = request.args.get('page', 1, type=int)
    
    paginated = StockRequest.query.filter_by(status='pending').order_by(
        StockRequest.request_date.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template(
        'admin/requests/list.html',
        requests=paginated.items,
        pagination=paginated,
        tab='pending'
    )


@employee_requests_bp.route('/admin/all', methods=['GET'])
@login_required
def admin_all_requests():
    """عرض جميع الطلبات للمسؤول"""
    # التحقق من صلاحية الموافقة على الطلبات
    if not current_user.has_granular_permission('requests_approve'):
        flash('ليس لديك صلاحية الموافقة على الطلبات', 'danger')
        return redirect(url_for('employee_requests.list_requests'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    
    query = StockRequest.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    paginated = query.order_by(
        StockRequest.request_date.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template(
        'admin/requests/list.html',
        requests=paginated.items,
        pagination=paginated,
        status_filter=status_filter,
        tab='all'
    )


@employee_requests_bp.route('/<request_id>/approve', methods=['POST'])
@login_required
def approve_request(request_id):
    """الموافقة على الطلب وخصم المخزون"""
    # التحقق من صلاحية الموافقة على الطلبات
    if not current_user.has_granular_permission('requests_approve'):
        flash('ليس لديك صلاحية الموافقة على الطلبات', 'danger')
        return redirect(url_for('employee_requests.list_requests'))
    
    try:
        stock_request = StockRequest.query.get_or_404(request_id)
        
        if stock_request.status != 'pending':
            flash('لا يمكن الموافقة على طلب غير معلق', 'warning')
            return redirect(url_for('employee_requests.view_request', request_id=request_id))
        
        # الموافقة على الطلب
        stock_request.status = 'approved'
        stock_request.approved_by_id = current_user.id
        stock_request.approval_date = dt.utcnow()
        stock_request.approver_signature_date = dt.utcnow()
        
        # خصم المخزون
        for idx, item in enumerate(stock_request.items):
            if item.quantity > 0:
                # تحديث رصيد المخزون
                item.item.quantity_in_stock -= item.quantity
                
                # إنشاء معاملة بمرجع فريد لكل عنصر
                unique_ref = f"{stock_request.request_number}-{idx+1}"
                transaction = Transaction(
                    item_id=item.item_id,
                    transaction_type=TransactionType.ISSUE.value,
                    quantity=item.quantity,
                    reference_number=unique_ref,
                    created_by_id=current_user.id,
                    description=f'طلب من: {stock_request.requested_by.full_name}'
                )
                db.session.add(transaction)
                
                # تحديث حالة العنصر
                item.item_status = 'delivered'
                item.delivered_quantity = item.quantity
        
        # تسجيل النشاط
        activity = ActivityLog(
            user_id=current_user.id,
            action='الموافقة على طلب منتجات',
            entity_type='StockRequest',
            entity_id=stock_request.id,
            new_value=f"الطلب رقم {stock_request.request_number} - موافقة"
        )
        db.session.add(activity)
        
        # إنشاء إشعار للموظف
        notification = Notification(
            user_id=stock_request.requested_by_id,
            title='تمت الموافقة على طلبك',
            message=f'تمت الموافقة على الطلب {stock_request.request_number} من قبل {current_user.full_name}',
            notification_type='request_approved',
            entity_type='StockRequest',
            entity_id=stock_request.id,
            priority='high'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        flash('تمت الموافقة على الطلب وخصم المخزون', 'success')
        return redirect(url_for('employee_requests.view_request', request_id=request_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في الموافقة على الطلب: {str(e)}', 'danger')
        return redirect(url_for('employee_requests.view_request', request_id=request_id))


@employee_requests_bp.route('/<request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    """رفض الطلب"""
    # التحقق من صلاحية الموافقة على الطلبات
    if not current_user.has_granular_permission('requests_approve'):
        flash('ليس لديك صلاحية الموافقة على الطلبات', 'danger')
        return redirect(url_for('employee_requests.list_requests'))
    
    try:
        stock_request = StockRequest.query.get_or_404(request_id)
        
        if stock_request.status != 'pending':
            flash('لا يمكن رفض طلب غير معلق', 'warning')
            return redirect(url_for('employee_requests.view_request', request_id=request_id))
        
        rejection_reason = request.form.get('rejection_reason', '')
        
        stock_request.status = 'rejected'
        stock_request.rejection_reason = rejection_reason
        stock_request.approved_by_id = current_user.id
        stock_request.approval_date = dt.utcnow()
        
        # تسجيل النشاط
        activity = ActivityLog(
            user_id=current_user.id,
            action='رفض طلب منتجات',
            entity_type='StockRequest',
            entity_id=stock_request.id,
            new_value=f"الطلب رقم {stock_request.request_number} - رفض"
        )
        db.session.add(activity)
        
        # إنشاء إشعار للموظف
        notification = Notification(
            user_id=stock_request.requested_by_id,
            title='تم رفض طلبك',
            message=f'تم رفض الطلب {stock_request.request_number}. السبب: {rejection_reason}',
            notification_type='request_rejected',
            entity_type='StockRequest',
            entity_id=stock_request.id,
            priority='normal'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        flash('تم رفض الطلب', 'success')
        return redirect(url_for('employee_requests.view_request', request_id=request_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في رفض الطلب: {str(e)}', 'danger')
        return redirect(url_for('employee_requests.view_request', request_id=request_id))


@employee_requests_bp.route('/<request_id>/receipt', methods=['GET'])
@login_required
def print_receipt(request_id):
    """طباعة وصل الطلب"""
    stock_request = StockRequest.query.get_or_404(request_id)
    
    # التحقق من الصلاحيات
    is_owner = stock_request.requested_by_id == current_user.id
    can_view_all = current_user.has_granular_permission('requests_view_all')
    can_view_own = current_user.has_granular_permission('requests_view_own')
    
    if not ((is_owner and can_view_own) or can_view_all):
        flash('ليس لديك صلاحية لطباعة هذا الوصل', 'danger')
        return redirect(url_for('employee_requests.list_requests'))
    
    from models import OrganizationSettings
    org_settings = OrganizationSettings.query.first()
    
    return render_template(
        'employee_requests/receipt.html',
        request=stock_request,
        org_settings=org_settings
    )


@employee_requests_bp.route('/api/items', methods=['GET'])
@login_required
def api_get_items():
    """API للحصول على المنتجات حسب الصنف"""
    # التحقق من صلاحية الوصول
    if not current_user.has_granular_permission('requests_create'):
        return jsonify({'error': 'ليس لديك صلاحية'}), 403
    
    category_id = request.args.get('category_id', None)
    search = request.args.get('search', '').lower()
    
    query = Item.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            (Item.name.ilike(f'%{search}%')) | 
            (Item.code.ilike(f'%{search}%'))
        )
    
    items = query.limit(50).all()
    
    return jsonify([{
        'id': item.id,
        'code': item.code,
        'name': item.name,
        'unit': item.unit,
        'quantity_in_stock': item.quantity_in_stock,
        'unit_price': item.unit_price or 0,
        'category': item.category.name if item.category else ''
    } for item in items])


def _send_request_notification(stock_request):
    """إرسال إشعار للمسؤولين عند تقديم طلب جديد"""
    # الحصول على جميع المسؤولين
    approvers = User.query.filter(
        User.role.in_([
            UserRole.WAREHOUSE_MANAGER.value,
            UserRole.ACCOUNTANT.value,
            UserRole.DIRECTOR.value,
            UserRole.ADMIN.value
        ]),
        User.is_active == True
    ).all()
    
    for approver in approvers:
        notification = Notification(
            user_id=approver.id,
            title='طلب منتجات جديد',
            message=f'الموظف {stock_request.requested_by.full_name} قدم طلب جديد: {stock_request.request_number}',
            notification_type='new_request',
            entity_type='StockRequest',
            entity_id=stock_request.id,
            priority='high'
        )
        db.session.add(notification)
    
    db.session.commit()