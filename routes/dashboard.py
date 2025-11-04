from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import (
    db, Item, User, PurchaseOrder, Transaction, 
    OrganizationSettings, AssetRegistration, MealRecord, ItemCategory_Model
)
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from permissions_config import PERMISSIONS

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """لوحة التحكم - توجيه إلى الصفحة المناسبة"""
    
    # التحقق من صلاحية عرض لوحة التحكم الرئيسية
    if current_user.has_granular_permission('dashboard_view'):
        return redirect(url_for('dashboard.admin_dashboard'))
    else:
        return redirect(url_for('dashboard.employee_dashboard'))

@dashboard_bp.route('/admin')
@login_required
def admin_dashboard():
    """لوحة التحكم الرئيسية للمديرين"""
    
    # التحقق من الصلاحية
    if not current_user.has_granular_permission('dashboard_view'):
        return render_template('403.html'), 403
    
    # إحصائيات عامة
    total_items = Item.query.count()
    total_users = User.query.count()
    total_suppliers = PurchaseOrder.query.distinct(PurchaseOrder.supplier_id).count()
    
    # الأصناف منخفضة المخزون
    low_stock_items = Item.query.filter(
        Item.quantity_in_stock <= Item.minimum_quantity
    ).all()
    
    # آخر العمليات
    recent_transactions = Transaction.query.order_by(
        Transaction.transaction_date.desc()
    ).limit(10).all()
    
    # إحصائيات المخزون
    total_stock_value = db.session.query(
        func.sum(Item.quantity_in_stock * Item.unit_price)
    ).scalar() or 0
    
    # آخر أوامر الشراء
    pending_orders = PurchaseOrder.query.filter_by(
        status='pending'
    ).order_by(PurchaseOrder.order_date.desc()).limit(5).all()
    
    # الوجبات اليومية
    today = datetime.utcnow().date()
    today_meals = MealRecord.query.filter_by(record_date=today).all()
    
    # معلومات المؤسسة
    org_settings = OrganizationSettings.query.first()
    
    stats = {
        'total_items': total_items,
        'total_users': total_users,
        'total_suppliers': total_suppliers,
        'low_stock_items': len(low_stock_items),
        'total_stock_value': total_stock_value,
        'pending_orders': len(pending_orders),
    }
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        low_stock_items=low_stock_items[:10],
        recent_transactions=recent_transactions,
        pending_orders=pending_orders,
        today_meals=today_meals,
        org_settings=org_settings,
    )

@dashboard_bp.route('/employee')
@login_required
def employee_dashboard():
    """لوحة تحكم الموظفين - تعرض فقط الصلاحيات المسموح بها"""
    
    # التحقق من صلاحية عرض لوحة التحكم الخاصة بالموظفين
    if not current_user.has_granular_permission('employee_dashboard_view') and not current_user.has_granular_permission('dashboard_view'):
        return render_template('403.html'), 403
    
    # الحصول على جميع صلاحيات المستخدم
    user_permissions = current_user.get_all_permissions()
    
    # بناء قائمة الوحدات المسموح بها
    allowed_modules = []
    
    # تنظيم الوحدات حسب الصلاحيات
    module_config = {
        'inventory': {
            'name': 'إدارة المخزون',
            'icon': 'fas fa-warehouse',
            'color': 'info',
            'permissions': ['inventory_view_items', 'inventory_add_transaction'],
            'links': [
                {'title': 'عرض الأصناف', 'url': 'inventory.items', 'permission': 'inventory_view_items', 'icon': 'fas fa-list'},
                {'title': 'إضافة عملية', 'url': 'inventory.add_transaction', 'permission': 'inventory_add_transaction', 'icon': 'fas fa-plus'},
            ]
        },
        'equipment': {
            'name': 'إدارة الأصول',
            'icon': 'fas fa-tools',
            'color': 'warning',
            'permissions': ['equipment_view_assets', 'equipment_add_issue'],
            'links': [
                {'title': 'عرض الأصول', 'url': 'equipment.assets', 'permission': 'equipment_view_assets', 'icon': 'fas fa-list'},
                {'title': 'تسليم أصل', 'url': 'equipment.add_issue', 'permission': 'equipment_add_issue', 'icon': 'fas fa-plus'},
            ]
        },
        'restaurant': {
            'name': 'إدارة المطعم',
            'icon': 'fas fa-utensils',
            'color': 'danger',
            'permissions': ['restaurant_view_recipes', 'restaurant_add_meal'],
            'links': [
                {'title': 'عرض الوصفات', 'url': 'restaurant.recipes', 'permission': 'restaurant_view_recipes', 'icon': 'fas fa-list'},
                {'title': 'تسجيل وجبة', 'url': 'restaurant.add_meal', 'permission': 'restaurant_add_meal', 'icon': 'fas fa-plus'},
            ]
        },
        'suppliers': {
            'name': 'إدارة الموردين',
            'icon': 'fas fa-handshake',
            'color': 'success',
            'permissions': ['suppliers_view_orders', 'suppliers_add_order'],
            'links': [
                {'title': 'عرض الأوامر', 'url': 'suppliers.orders', 'permission': 'suppliers_view_orders', 'icon': 'fas fa-list'},
                {'title': 'إنشاء أمر شراء', 'url': 'suppliers.add_order', 'permission': 'suppliers_add_order', 'icon': 'fas fa-plus'},
            ]
        },
        'employee_requests': {
            'name': 'طلباتي الشخصية',
            'icon': 'fas fa-clipboard-list',
            'color': 'primary',
            'permissions': ['requests_create', 'requests_view_own'],
            'links': [
                {'title': 'عرض طلباتي', 'url': 'employee_requests.list_requests', 'permission': 'requests_view_own', 'icon': 'fas fa-list'},
                {'title': 'إنشاء طلب جديد', 'url': 'employee_requests.create_request', 'permission': 'requests_create', 'icon': 'fas fa-plus'},
            ]
        },
        'reports': {
            'name': 'التقارير',
            'icon': 'fas fa-chart-bar',
            'color': 'secondary',
            'permissions': ['reports_inventory_movement', 'reports_low_stock'],
            'links': [
                {'title': 'تقرير حركة المخزون', 'url': 'reports.inventory_movement', 'permission': 'reports_inventory_movement', 'icon': 'fas fa-chart-line'},
                {'title': 'تقرير الأصناف منخفضة', 'url': 'reports.low_stock', 'permission': 'reports_low_stock', 'icon': 'fas fa-exclamation'},
            ]
        },
    }
    
    # تصفية الوحدات حسب الصلاحيات
    for module_key, module_data in module_config.items():
        # التحقق من وجود صلاحية واحدة على الأقل في هذه الوحدة
        has_any_permission = any(
            perm in user_permissions for perm in module_data['permissions']
        )
        
        if has_any_permission:
            # تصفية الروابط حسب الصلاحيات
            filtered_links = [
                link for link in module_data['links']
                if link['permission'] in user_permissions
            ]
            
            if filtered_links:
                allowed_modules.append({
                    'key': module_key,
                    'name': module_data['name'],
                    'icon': module_data['icon'],
                    'color': module_data['color'],
                    'links': filtered_links,
                    'link_count': len(filtered_links)
                })
    
    # معلومات المؤسسة
    org_settings = OrganizationSettings.query.first()
    
    # إحصائيات بسيطة
    stats = {
        'modules_count': len(allowed_modules),
        'permissions_count': len(user_permissions),
        'total_links': sum(m['link_count'] for m in allowed_modules)
    }
    
    return render_template(
        'dashboard/employee_dashboard.html',
        allowed_modules=allowed_modules,
        org_settings=org_settings,
        stats=stats,
        current_user=current_user,
    )

@dashboard_bp.route('/statistics')
@login_required
def statistics():
    """الإحصائيات التفصيلية"""
    
    # إحصائيات الدخول والخروج
    from_date = datetime.utcnow() - timedelta(days=30)
    to_date = datetime.utcnow()
    
    # العمليات حسب النوع
    transactions_by_type = db.session.query(
        Transaction.transaction_type,
        func.count(Transaction.id)
    ).filter(
        Transaction.transaction_date.between(from_date, to_date)
    ).group_by(Transaction.transaction_type).all()
    
    # القيمة الإجمالية للعمليات
    total_value_by_type = db.session.query(
        Transaction.transaction_type,
        func.sum(Transaction.total_value)
    ).filter(
        Transaction.transaction_date.between(from_date, to_date)
    ).group_by(Transaction.transaction_type).all()
    
    # استهلاك المخزون حسب الفئة
    consumption_by_category = db.session.query(
        ItemCategory_Model.name,
        func.sum(Transaction.quantity)
    ).join(
        Item, Item.id == Transaction.item_id
    ).join(
        ItemCategory_Model, ItemCategory_Model.id == Item.category_id
    ).filter(
        Transaction.transaction_type == 'issue',
        Transaction.transaction_date.between(from_date, to_date)
    ).group_by(ItemCategory_Model.name).all()
    
    return render_template(
        'dashboard/statistics.html',
        transactions_by_type=transactions_by_type,
        total_value_by_type=total_value_by_type,
        consumption_by_category=consumption_by_category,
    )