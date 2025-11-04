from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, current_app
)
from flask_login import login_required, current_user
from models import (
    db, Item, ItemCategory_Model, Transaction, 
    User, UserRole, ActivityLog,
    # الميزات الجديدة
    InventoryABCAnalysis, InventoryCount, InventoryCountItem,
    Warehouse, WarehouseInventory, InventoryCostAnalysis,
    RecommendedOrder, InventoryForecast, PriceHistory,
    SupplierPerformance, QRBarcodeConfig, QRBarcodeScan,
    SmartInventoryAlert, Supplier
)
from datetime import datetime, timedelta, date
import uuid
from auth_helpers import require_granular_permission
from sqlalchemy import func, and_

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# ==================== Categories ====================

@inventory_bp.route('/categories')
@login_required
def categories():
    """قائمة تصنيفات الأصناف"""
    # التحقق من صلاحية عرض الفئات
    if not current_user.has_granular_permission('inventory_view_categories'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    categories = ItemCategory_Model.query.all()
    can_add = current_user.has_granular_permission('inventory_add_category')
    can_edit = current_user.has_granular_permission('inventory_edit_category')
    
    return render_template('inventory/categories.html', categories=categories, 
                          can_add=can_add, can_edit=can_edit)

@inventory_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """إضافة تصنيف جديد"""
    # التحقق من صلاحية الإضافة
    if not current_user.has_granular_permission('inventory_add_category'):
        flash('ليس لديك صلاحية لإضافة فئات', 'danger')
        return redirect(url_for('inventory.categories'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()
        category_type = request.form.get('category_type', '').strip()
        
        if not code or not name or not category_type:
            flash('جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('inventory.add_category'))
        
        if ItemCategory_Model.query.filter_by(code=code).first():
            flash('هذا الكود موجود بالفعل', 'danger')
            return redirect(url_for('inventory.add_category'))
        
        category = ItemCategory_Model(
            code=code,
            name=name,
            category_type=category_type,
            description=request.form.get('description', '')
        )
        
        db.session.add(category)
        db.session.commit()
        
        # تسجيل النشاط
        log_activity(
            user_id=current_user.id,
            action=f"إضافة تصنيف جديد: {name}",
            entity_type='ItemCategory',
            entity_id=str(category.id)
        )
        
        flash('تم إضافة التصنيف بنجاح', 'success')
        return redirect(url_for('inventory.categories'))
    
    return render_template('inventory/add_category.html')

@inventory_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """تعديل تصنيف"""
    # التحقق من صلاحية التعديل
    if not current_user.has_granular_permission('inventory_edit_category'):
        flash('ليس لديك صلاحية لتعديل الفئات', 'danger')
        return redirect(url_for('inventory.categories'))
    
    category = ItemCategory_Model.query.get_or_404(category_id)
    
    if request.method == 'POST':
        old_name = category.name
        
        category.code = request.form.get('code', category.code)
        category.name = request.form.get('name', category.name)
        category.category_type = request.form.get('category_type', category.category_type)
        category.description = request.form.get('description', category.description)
        
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action=f"تعديل تصنيف: من {old_name} إلى {category.name}",
            entity_type='ItemCategory',
            entity_id=str(category.id),
            old_value=old_name,
            new_value=category.name
        )
        
        flash('تم تحديث التصنيف بنجاح', 'success')
        return redirect(url_for('inventory.categories'))
    
    return render_template('inventory/edit_category.html', category=category)

# ==================== Items ====================

@inventory_bp.route('/items')
@login_required
def items():
    """قائمة الأصناف"""
    # التحقق من صلاحية عرض الأصناف
    if not current_user.has_granular_permission('inventory_view_items'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    
    query = Item.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            (Item.code.ilike(f'%{search}%')) |
            (Item.name.ilike(f'%{search}%'))
        )
    
    items = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    categories = ItemCategory_Model.query.all()
    can_add = current_user.has_granular_permission('inventory_add_item')
    can_edit = current_user.has_granular_permission('inventory_edit_item')
    can_delete = current_user.has_granular_permission('inventory_delete_item')
    
    return render_template(
        'inventory/items.html',
        items=items,
        categories=categories,
        selected_category=category_id,
        search=search,
        can_add=can_add,
        can_edit=can_edit,
        can_delete=can_delete
    )

@inventory_bp.route('/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """إضافة صنف جديد"""
    # التحقق من صلاحية الإضافة
    if not current_user.has_granular_permission('inventory_add_item'):
        flash('ليس لديك صلاحية لإضافة أصناف', 'danger')
        return redirect(url_for('inventory.items'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        
        if not code or not name or not category_id:
            flash('جميع الحقول المطلوبة يجب ملؤها', 'warning')
            return redirect(url_for('inventory.add_item'))
        
        if Item.query.filter_by(code=code).first():
            flash('هذا الكود موجود بالفعل', 'danger')
            return redirect(url_for('inventory.add_item'))
        
        item = Item(
            code=code,
            name=name,
            category_id=category_id,
            description=request.form.get('description', ''),
            unit=request.form.get('unit', 'قطعة'),
            minimum_quantity=float(request.form.get('minimum_quantity', 0)) or 0,
            unit_price=float(request.form.get('unit_price', 0)) or None,
        )
        
        db.session.add(item)
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action=f"إضافة صنف جديد: {name}",
            entity_type='Item',
            entity_id=item.id
        )
        
        flash('تم إضافة الصنف بنجاح', 'success')
        return redirect(url_for('inventory.items'))
    
    categories = ItemCategory_Model.query.filter_by(is_active=True).all()
    return render_template('inventory/add_item.html', categories=categories)

@inventory_bp.route('/items/edit/<item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    """تعديل صنف"""
    # التحقق من صلاحية التعديل
    if not current_user.has_granular_permission('inventory_edit_item'):
        flash('ليس لديك صلاحية لتعديل الأصناف', 'danger')
        return redirect(url_for('inventory.items'))
    
    item = Item.query.get_or_404(item_id)
    
    if request.method == 'POST':
        old_name = item.name
        
        item.name = request.form.get('name', item.name)
        item.category_id = request.form.get('category_id', item.category_id)
        item.description = request.form.get('description', item.description)
        item.unit = request.form.get('unit', item.unit)
        item.minimum_quantity = float(request.form.get('minimum_quantity', item.minimum_quantity)) or 0
        item.unit_price = float(request.form.get('unit_price', item.unit_price)) or None
        
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action=f"تعديل صنف: {old_name}",
            entity_type='Item',
            entity_id=item.id,
            old_value=old_name,
            new_value=item.name
        )
        
        flash('تم تحديث الصنف بنجاح', 'success')
        return redirect(url_for('inventory.items'))
    
    categories = ItemCategory_Model.query.filter_by(is_active=True).all()
    return render_template('inventory/edit_item.html', item=item, categories=categories)

# ==================== Transactions ====================

@inventory_bp.route('/transactions')
@login_required
def transactions():
    """قائمة العمليات"""
    # التحقق من صلاحية عرض العمليات
    if not current_user.has_granular_permission('inventory_view_transactions'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    transaction_type = request.args.get('transaction_type', '')
    
    query = Transaction.query
    
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    
    paginated = query.order_by(Transaction.transaction_date.desc()).paginate(
        page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 20)
    )
    
    return render_template(
        'inventory/transactions.html',
        transactions=paginated.items,
        pages=paginated.pages,
        current_page=paginated.page,
        selected_type=transaction_type
    )

@inventory_bp.route('/transactions/<transaction_id>')
@login_required
def view_transaction(transaction_id):
    """عرض تفاصيل العملية"""
    transaction = Transaction.query.get_or_404(transaction_id)
    return render_template('inventory/view_transaction.html', transaction=transaction)

@inventory_bp.route('/transactions/<transaction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    """تعديل عملية"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # السماح بالتعديل فقط للعمليات المسموح بها
    if transaction.transaction_type not in ['adjustment', 'issue', 'return']:
        flash('لا يمكن تعديل هذا النوع من العمليات', 'danger')
        return redirect(url_for('inventory.transactions'))
    
    if request.method == 'POST':
        old_quantity = transaction.quantity
        
        # حساب الفرق في الكمية
        new_quantity = float(request.form.get('quantity', transaction.quantity))
        quantity_diff = new_quantity - old_quantity
        
        # تحديث كمية المخزون
        if transaction.transaction_type in ['adjustment', 'issue', 'return']:
            if transaction.transaction_type == 'issue':
                transaction.item.quantity_in_stock -= quantity_diff
            elif transaction.transaction_type in ['adjustment', 'return']:
                transaction.item.quantity_in_stock += quantity_diff
        
        transaction.quantity = new_quantity
        transaction.unit_price = float(request.form.get('unit_price', transaction.unit_price or 0)) or None
        transaction.total_value = transaction.quantity * transaction.unit_price if transaction.unit_price else None
        transaction.description = request.form.get('description', transaction.description)
        
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action=f"تعديل عملية: {transaction.reference_number}",
            entity_type='Transaction',
            entity_id=transaction.id,
            old_value=f"الكمية: {old_quantity}",
            new_value=f"الكمية: {transaction.quantity}"
        )
        
        flash('تم تحديث العملية بنجاح', 'success')
        return redirect(url_for('inventory.transactions'))
    
    return render_template('inventory/edit_transaction.html', transaction=transaction)

@inventory_bp.route('/transactions/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """إضافة عملية جديدة"""
    if request.method == 'POST':
        item_id = request.form.get('item_id', '')
        transaction_type = request.form.get('transaction_type', '')
        quantity = float(request.form.get('quantity', 0))
        
        if not item_id or not transaction_type or quantity <= 0:
            flash('بيانات غير صحيحة', 'warning')
            return redirect(url_for('inventory.add_transaction'))
        
        item = Item.query.get_or_404(item_id)
        
        # التحقق من وجود كمية كافية للإخراج
        if transaction_type == 'issue' and item.quantity_in_stock < quantity:
            flash(f'الكمية الموجودة ({item.quantity_in_stock}) أقل من المطلوبة', 'danger')
            return redirect(url_for('inventory.add_transaction'))
        
        # تحديث المخزون
        if transaction_type in ['purchase', 'return']:
            item.quantity_in_stock += quantity
        elif transaction_type == 'issue':
            item.quantity_in_stock -= quantity
        
        # معالجة سعر الوحدة
        unit_price_str = request.form.get('unit_price', '').strip()
        try:
            unit_price = float(unit_price_str) if unit_price_str else (item.unit_price or 0)
        except ValueError:
            unit_price = item.unit_price or 0
        
        # حساب القيمة الإجمالية
        total_value = quantity * unit_price if unit_price else None
        
        transaction = Transaction(
            reference_number=f"TRN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}",
            transaction_type=transaction_type,
            item_id=item_id,
            quantity=quantity,
            unit_price=unit_price,
            total_value=total_value,
            from_location=request.form.get('from_location', ''),
            to_location=request.form.get('to_location', ''),
            created_by_id=current_user.id,
            description=request.form.get('description', '')
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        log_activity(
            user_id=current_user.id,
            action=f"عملية {transaction_type}: {item.name}",
            entity_type='Transaction',
            entity_id=transaction.id,
            new_value=f"الكمية: {quantity}"
        )
        
        flash(f'تم تسجيل العملية بنجاح - {transaction.reference_number}', 'success')
        return redirect(url_for('inventory.transactions'))
    
    items = Item.query.filter_by(is_active=True).all()
    return render_template('inventory/add_transaction.html', items=items)


# ==================== 1. تحليل ABC للمخزون ====================

@inventory_bp.route('/abc-analysis')
@login_required
def abc_analysis():
    """عرض تحليل ABC للمخزون"""
    if not current_user.has_granular_permission('inventory_view_abc_analysis'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    period = request.args.get('period', 'yearly')
    category_filter = request.args.get('category', '')
    
    # جلب جميع الأصناف مع معلومات ABC
    items = Item.query.all()
    if category_filter:
        items = Item.query.filter_by(category_id=int(category_filter)).all()
    
    # حساب القيم
    total_value = sum(item.quantity_in_stock * (item.unit_price or 0) for item in items)
    
    # إضافة معلومات ABC لكل صنف
    for item in items:
        analysis = InventoryABCAnalysis.query.filter_by(item_id=item.id, period=period).first()
        if analysis:
            item.abc_classification = analysis.abc_category
            item.percentage_of_total = analysis.percentage_of_total
        else:
            item.abc_classification = 'C'
            item.percentage_of_total = 0
    
    # جلب الفئات
    categories = ItemCategory_Model.query.all()
    
    # حساب الإحصائيات
    total_items = len(items)
    category_counts = {
        'A': len([i for i in items if getattr(i, 'abc_classification', 'C') == 'A']),
        'B': len([i for i in items if getattr(i, 'abc_classification', 'C') == 'B']),
        'C': len([i for i in items if getattr(i, 'abc_classification', 'C') == 'C'])
    }
    
    return render_template('inventory/abc_analysis.html', 
                          items=items, period=period, categories=categories,
                          total_items=total_items, total_value=total_value,
                          category_counts=category_counts)


@inventory_bp.route('/abc-analysis/regenerate', methods=['POST'])
@login_required
def regenerate_abc_analysis():
    """إعادة حساب تحليل ABC"""
    if not current_user.has_granular_permission('inventory_edit_abc_analysis'):
        flash('ليس لديك صلاحية لتحديث التحليل', 'danger')
        return redirect(url_for('inventory.abc_analysis'))
    
    period = request.form.get('period', 'yearly')
    
    # حذف التحليلات السابقة
    InventoryABCAnalysis.query.filter_by(period=period).delete()
    
    # حساب الاستهلاك والقيمة لكل صنف
    items = Item.query.all()
    analyses_data = []
    
    for item in items:
        transactions = Transaction.query.filter_by(item_id=item.id).all()
        
        annual_consumption = sum(t.quantity for t in transactions)
        annual_value = sum(t.total_value or 0 for t in transactions)
        
        if annual_value > 0:
            analyses_data.append({
                'item': item,
                'annual_consumption': annual_consumption,
                'annual_value': annual_value
            })
    
    # ترتيب حسب القيمة السنوية
    analyses_data.sort(key=lambda x: x['annual_value'], reverse=True)
    
    total_value = sum(a['annual_value'] for a in analyses_data)
    cumulative_percentage = 0
    
    for data in analyses_data:
        percentage = (data['annual_value'] / total_value * 100) if total_value > 0 else 0
        cumulative_percentage += percentage
        
        # تحديد الفئة
        if cumulative_percentage <= 80:
            abc_category = 'A'
        elif cumulative_percentage <= 95:
            abc_category = 'B'
        else:
            abc_category = 'C'
        
        analysis = InventoryABCAnalysis(
            item_id=data['item'].id,
            analysis_date=date.today(),
            period=period,
            abc_category=abc_category,
            annual_consumption=data['annual_consumption'],
            annual_value=data['annual_value'],
            consumption_rate=data['annual_consumption'] / 12 if period == 'yearly' else data['annual_consumption'],
            percentage_of_total=percentage
        )
        db.session.add(analysis)
    
    db.session.commit()
    flash(f'تم تحديث تحليل ABC بنجاح - {len(analyses_data)} صنف', 'success')
    return redirect(url_for('inventory.abc_analysis'))


# ==================== 2. عمليات الجرد الدورية ====================

@inventory_bp.route('/inventory-counts')
@login_required
def inventory_counts():
    """قائمة عمليات الجرد"""
    if not current_user.has_granular_permission('inventory_view_counts'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    counts = InventoryCount.query.paginate(page=page, per_page=10)
    
    return render_template('inventory/inventory_counts.html', counts=counts)


@inventory_bp.route('/inventory-counts/new', methods=['GET', 'POST'])
@login_required
def new_inventory_count():
    """بدء عملية جرد جديدة"""
    if not current_user.has_granular_permission('inventory_add_count'):
        flash('ليس لديك صلاحية لإنشاء عملية جرد', 'danger')
        return redirect(url_for('inventory.inventory_counts'))
    
    if request.method == 'POST':
        count_type = request.form.get('count_type', 'full')
        warehouse_location = request.form.get('warehouse_location', '')
        
        count = InventoryCount(
            count_number=f"COUNT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            count_type=count_type,
            count_date=datetime.utcnow(),
            warehouse_location=warehouse_location,
            started_by_id=current_user.id
        )
        
        db.session.add(count)
        db.session.flush()
        
        # إضافة الأصناف
        items = Item.query.filter_by(is_active=True).all()
        for item in items:
            count_item = InventoryCountItem(
                count_id=count.id,
                item_id=item.id,
                system_quantity=item.quantity_in_stock
            )
            db.session.add(count_item)
        
        db.session.commit()
        flash(f'تم إنشاء عملية جرد جديدة: {count.count_number}', 'success')
        return redirect(url_for('inventory.edit_inventory_count', count_id=count.id))
    
    return render_template('inventory/new_inventory_count.html')


@inventory_bp.route('/inventory-counts/<count_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_inventory_count(count_id):
    """تحرير عملية جرد"""
    count = InventoryCount.query.get_or_404(count_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_item':
            item_id = request.form.get('item_id')
            physical_count = float(request.form.get('physical_count', 0))
            variance_reason = request.form.get('variance_reason', '')
            
            count_item = InventoryCountItem.query.filter_by(
                count_id=count_id,
                item_id=item_id
            ).first_or_404()
            
            count_item.physical_count = physical_count
            count_item.variance = physical_count - count_item.system_quantity
            count_item.variance_percentage = (count_item.variance / count_item.system_quantity * 100) if count_item.system_quantity > 0 else 0
            count_item.variance_reason = variance_reason
            
            db.session.commit()
            flash('تم تحديث البيانات', 'success')
        
        elif action == 'complete':
            count.status = 'completed'
            count.completed_by_id = current_user.id
            count.completed_at = datetime.utcnow()
            db.session.commit()
            flash('تم إغلاق عملية الجرد', 'success')
            return redirect(url_for('inventory.inventory_counts'))
    
    return render_template('inventory/edit_inventory_count.html', count=count)


# ==================== 3. إدارة المستودعات ====================

@inventory_bp.route('/warehouses')
@login_required
def warehouses():
    """قائمة المستودعات"""
    if not current_user.has_granular_permission('inventory_view_warehouses'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    warehouses_list = Warehouse.query.all()
    return render_template('inventory/warehouses.html', warehouses=warehouses_list)


@inventory_bp.route('/warehouses/add', methods=['GET', 'POST'])
@login_required
def add_warehouse():
    """إضافة مستودع جديد"""
    if not current_user.has_granular_permission('inventory_add_warehouse'):
        flash('ليس لديك صلاحية لإضافة مستودعات', 'danger')
        return redirect(url_for('inventory.warehouses'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        
        if not code or not name or not location:
            flash('جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('inventory.add_warehouse'))
        
        warehouse = Warehouse(
            code=code,
            name=name,
            location=location,
            address=request.form.get('address', ''),
            capacity=float(request.form.get('capacity', 0)) if request.form.get('capacity') else None
        )
        
        db.session.add(warehouse)
        db.session.commit()
        flash('تم إضافة المستودع بنجاح', 'success')
        return redirect(url_for('inventory.warehouses'))
    
    return render_template('inventory/add_warehouse.html')


@inventory_bp.route('/warehouse/<warehouse_id>/inventory')
@login_required
def warehouse_inventory(warehouse_id):
    """عرض مخزون المستودع"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    if not current_user.has_granular_permission('inventory_view_warehouse_items'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    inventory_items = WarehouseInventory.query.filter_by(warehouse_id=warehouse_id).all()
    
    return render_template('inventory/warehouse_inventory.html', 
                          warehouse=warehouse, inventory_items=inventory_items)


# ==================== 4. تكاليف المخزون ====================

@inventory_bp.route('/cost-analysis')
@login_required
def cost_analysis():
    """تحليل تكاليف المخزون"""
    if not current_user.has_granular_permission('inventory_view_cost_analysis'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    period = request.args.get('period', 'monthly')
    
    # جلب جميع الأصناف
    items = Item.query.all()
    
    # حساب الإحصائيات
    total_inventory_value = sum(item.quantity_in_stock * (item.unit_price or 0) for item in items)
    average_unit_price = (sum(item.unit_price or 0 for item in items) / len(items)) if items else 0
    max_item_value = max((item.quantity_in_stock * (item.unit_price or 0) for item in items), default=0)
    
    return render_template('inventory/cost_analysis.html', 
                          items=items, period=period,
                          total_inventory_value=total_inventory_value,
                          average_unit_price=average_unit_price,
                          max_item_value=max_item_value)


@inventory_bp.route('/cost-analysis/recalculate', methods=['POST'])
@login_required
def recalculate_cost_analysis():
    """إعادة حساب تكاليف المخزون"""
    if not current_user.has_granular_permission('inventory_edit_cost_analysis'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('inventory.cost_analysis'))
    
    period = request.form.get('period', 'monthly')
    
    # حذف التحليلات السابقة
    InventoryCostAnalysis.query.filter_by(period=period).delete()
    
    items = Item.query.all()
    
    for item in items:
        transactions = Transaction.query.filter_by(item_id=item.id).all()
        
        total_value = sum(t.total_value or 0 for t in transactions)
        avg_inventory = item.quantity_in_stock
        
        # حساب التكاليف
        holding_cost = (total_value * 20) / 100  # افترض 20% تكلفة احتفاظ
        ordering_cost = len(transactions) * 50  # افترض 50 لكل عملية طلب
        
        analysis = InventoryCostAnalysis(
            item_id=item.id,
            analysis_date=date.today(),
            period=period,
            holding_cost=holding_cost,
            ordering_cost=ordering_cost,
            total_inventory_value=total_value,
            average_inventory=avg_inventory,
            profitability=total_value - holding_cost
        )
        db.session.add(analysis)
    
    db.session.commit()
    flash('تم تحديث تحليل التكاليف', 'success')
    return redirect(url_for('inventory.cost_analysis'))


# ==================== 5. التوصيات والطلبات ====================

@inventory_bp.route('/recommendations')
@login_required
def recommendations():
    """عرض التوصيات"""
    if not current_user.has_granular_permission('inventory_view_recommendations'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('dashboard.index'))
    
    status = request.args.get('status', 'pending')
    recommendations = RecommendedOrder.query.filter_by(status=status).all()
    
    return render_template('inventory/recommendations.html', 
                          recommendations=recommendations, status=status)


@inventory_bp.route('/recommendations/<rec_id>/approve', methods=['POST'])
@login_required
def approve_recommendation(rec_id):
    """الموافقة على التوصية"""
    if not current_user.has_granular_permission('inventory_approve_recommendation'):
        return jsonify({'error': 'No permission'}), 403
    
    rec = RecommendedOrder.query.get_or_404(rec_id)
    rec.status = 'approved'
    rec.processed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تمت الموافقة على التوصية'})


# ==================== 6. التنبؤات ====================

@inventory_bp.route('/forecasts')
@login_required
def forecasts():
    """عرض التنبؤات"""
    if not current_user.has_granular_permission('inventory_view_forecasts'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('dashboard.index'))
    
    forecast_period = request.args.get('period', 'next_month')
    item_id = request.args.get('item_id')
    
    query = InventoryForecast.query.filter_by(forecast_period=forecast_period)
    
    if item_id:
        query = query.filter_by(item_id=item_id)
    
    forecasts_data = query.all()
    
    # حساب متوسط الطلب المتوقع
    average_demand = (sum(f.forecasted_quantity or 0 for f in forecasts_data) / len(forecasts_data)) if forecasts_data else 0
    
    # جلب جميع الأصناف للفلتر
    items = Item.query.all()
    
    return render_template('inventory/forecasts.html', 
                          forecasts=forecasts_data, forecast_period=forecast_period,
                          average_demand=average_demand, items=items)


# ==================== 7. سجل الأسعار ====================

@inventory_bp.route('/price-history')
@login_required
def price_history():
    """عرض سجل الأسعار"""
    if not current_user.has_granular_permission('inventory_view_price_history'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('dashboard.index'))
    
    item_id = request.args.get('item_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # جلب البيانات
    query = PriceHistory.query
    
    if item_id:
        query = query.filter_by(item_id=item_id)
    
    if start_date:
        query = query.filter(PriceHistory.price_date >= start_date)
    if end_date:
        query = query.filter(PriceHistory.price_date <= end_date)
    
    price_changes = query.order_by(PriceHistory.price_date.desc()).all()
    
    items = Item.query.all()
    
    # حساب الإحصائيات
    average_price = (sum(p.unit_price or 0 for p in price_changes) / len(price_changes)) if price_changes else 0
    max_price = max((p.unit_price or 0 for p in price_changes), default=0)
    min_price = min((p.unit_price or 0 for p in price_changes), default=0) if price_changes else 0
    
    return render_template('inventory/price_history.html', 
                          price_changes=price_changes, items=items, selected_item=item_id,
                          average_price=average_price, max_price=max_price, min_price=min_price)


# ==================== 8. أداء الموردين ====================

@inventory_bp.route('/supplier-performance')
@login_required
def supplier_performance():
    """عرض أداء الموردين"""
    if not current_user.has_granular_permission('inventory_view_supplier_performance'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('dashboard.index'))
    
    performances = SupplierPerformance.query.all()
    
    return render_template('inventory/supplier_performance.html', performances=performances)


# ==================== 9. QR/Barcode ====================

@inventory_bp.route('/qrbarcode-config')
@login_required
def qrbarcode_config():
    """إعدادات QR/Barcode"""
    if not current_user.has_granular_permission('inventory_view_qrbarcode'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('dashboard.index'))
    
    configs = QRBarcodeConfig.query.all()
    
    return render_template('inventory/qrbarcode_config.html', configs=configs)


@inventory_bp.route('/qrbarcode-scan', methods=['POST'])
@login_required
def qrbarcode_scan():
    """تسجيل مسح QR/Barcode"""
    if not current_user.has_granular_permission('inventory_scan_qrbarcode'):
        return jsonify({'error': 'No permission'}), 403
    
    barcode_value = request.form.get('barcode_value')
    action = request.form.get('action', 'check_in')
    
    config = QRBarcodeConfig.query.filter_by(barcode_value=barcode_value).first()
    
    if not config:
        return jsonify({'error': 'Barcode not found'}), 404
    
    scan = QRBarcodeScan(
        config_id=config.id,
        item_id=config.item_id,
        user_id=current_user.id,
        scan_type='barcode',
        action=action,
        location=request.form.get('location', '')
    )
    
    db.session.add(scan)
    config.last_scanned = datetime.utcnow()
    config.scan_count += 1
    db.session.commit()
    
    return jsonify({'success': True, 'item': config.item.name})


# ==================== 10. الإنذارات الذكية ====================

@inventory_bp.route('/smart-alerts')
@login_required
def smart_alerts():
    """عرض الإنذارات الذكية"""
    if not current_user.has_granular_permission('inventory_view_smart_alerts'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('dashboard.index'))
    
    alert_type = request.args.get('type', 'all')
    
    if alert_type == 'all':
        alerts = SmartInventoryAlert.query.filter_by(is_resolved=False).all()
    else:
        alerts = SmartInventoryAlert.query.filter_by(
            alert_type=alert_type,
            is_resolved=False
        ).all()
    
    return render_template('inventory/smart_alerts.html', 
                          alerts=alerts, alert_type=alert_type)


@inventory_bp.route('/smart-alert/<alert_id>/resolve', methods=['POST'])
@login_required
def resolve_smart_alert(alert_id):
    """حل الإنذار"""
    if not current_user.has_granular_permission('inventory_resolve_alert'):
        return jsonify({'error': 'No permission'}), 403
    
    alert = SmartInventoryAlert.query.get_or_404(alert_id)
    alert.is_resolved = True
    alert.action_taken = request.form.get('action_taken', '')
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== Helper Functions ====================

def log_activity(user_id, action, entity_type=None, entity_id=None, old_value=None, new_value=None):
    """تسجيل نشاط"""
    from flask import request as flask_request
    
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=flask_request.remote_addr,
        user_agent=flask_request.user_agent.string
    )
    db.session.add(log)
    db.session.commit()