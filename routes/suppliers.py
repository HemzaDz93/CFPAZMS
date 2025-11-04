from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, current_app
)
from flask_login import login_required, current_user
from models import (
    db, Supplier, PurchaseOrder, PurchaseOrderItem, 
    Item, ActivityLog, UserRole
)
from datetime import datetime
import uuid
from auth_helpers import require_granular_permission

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@suppliers_bp.route('/')
@login_required
def suppliers():
    """قائمة الموردين"""
    # التحقق من صلاحية عرض الموردين
    if not current_user.has_granular_permission('suppliers_view'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Supplier.query
    
    # Filter by status if provided
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    if search:
        query = query.filter(
            (Supplier.code.ilike(f'%{search}%')) |
            (Supplier.name.ilike(f'%{search}%')) |
            (Supplier.phone.ilike(f'%{search}%')) |
            (Supplier.tax_id.ilike(f'%{search}%'))
        )
    
    suppliers = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    
    # Add order_count to each supplier for template
    for supplier in suppliers.items:
        supplier.order_count = len(supplier.purchase_orders)
    
    can_add = current_user.has_granular_permission('suppliers_add')
    can_edit = current_user.has_granular_permission('suppliers_edit')
    can_delete = current_user.has_granular_permission('suppliers_delete')
    
    return render_template(
        'suppliers/suppliers.html',
        suppliers=suppliers,
        search=search,
        selected_status=status,
        can_add=can_add,
        can_edit=can_edit,
        can_delete=can_delete
    )

@suppliers_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    """إضافة مورد جديد"""
    # التحقق من صلاحية الإضافة
    if not current_user.has_granular_permission('suppliers_add'):
        flash('ليس لديك صلاحية لإضافة موردين', 'danger')
        return redirect(url_for('suppliers.suppliers'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()
        
        if not code or not name:
            flash('الكود والاسم مطلوبان', 'warning')
            return redirect(url_for('suppliers.add_supplier'))
        
        if Supplier.query.filter_by(code=code).first():
            flash('هذا الكود موجود بالفعل', 'danger')
            return redirect(url_for('suppliers.add_supplier'))
        
        supplier = Supplier(
            code=code,
            name=name,
            description=request.form.get('description', ''),
            tax_id=request.form.get('tax_id', ''),
            registration_number=request.form.get('registration_number', ''),
            address=request.form.get('address', ''),
            city=request.form.get('city', ''),
            phone=request.form.get('phone', ''),
            email=request.form.get('email', ''),
            contact_person=request.form.get('contact_person', ''),
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"إضافة مورد جديد: {name}",
            entity_type='Supplier',
            entity_id=supplier.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم إضافة المورد بنجاح', 'success')
        return redirect(url_for('suppliers.suppliers'))
    
    return render_template('suppliers/add_supplier.html')

@suppliers_bp.route('/edit/<supplier_id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    """تعديل مورد"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    if request.method == 'POST':
        supplier.name = request.form.get('name', supplier.name)
        supplier.description = request.form.get('description', supplier.description)
        supplier.tax_id = request.form.get('tax_id', supplier.tax_id)
        supplier.registration_number = request.form.get('registration_number', supplier.registration_number)
        supplier.address = request.form.get('address', supplier.address)
        supplier.city = request.form.get('city', supplier.city)
        supplier.phone = request.form.get('phone', supplier.phone)
        supplier.email = request.form.get('email', supplier.email)
        supplier.contact_person = request.form.get('contact_person', supplier.contact_person)
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"تعديل مورد: {supplier.name}",
            entity_type='Supplier',
            entity_id=supplier.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تحديث بيانات المورد بنجاح', 'success')
        return redirect(url_for('suppliers.suppliers'))
    
    return render_template('suppliers/edit_supplier.html', supplier=supplier)

# ==================== Purchase Orders ====================

@suppliers_bp.route('/orders')
@login_required
def orders():
    """قائمة أوامر الشراء"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = PurchaseOrder.query
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(PurchaseOrder.order_date.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE']
    )
    
    return render_template('suppliers/orders.html', orders=orders, selected_status=status)

@suppliers_bp.route('/orders/add', methods=['GET', 'POST'])
@login_required
def add_order():
    """إضافة أمر شراء جديد"""
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id', '')
        
        if not supplier_id:
            flash('يجب اختيار مورد', 'warning')
            return redirect(url_for('suppliers.add_order'))
        
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Handle empty date fields
        expected_delivery = request.form.get('expected_delivery', '').strip()
        if expected_delivery:
            try:
                expected_delivery = datetime.strptime(expected_delivery, '%Y-%m-%d').date()
            except ValueError:
                expected_delivery = None
        else:
            expected_delivery = None
        
        purchase_order = PurchaseOrder(
            po_number=f"PO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6].upper()}",
            supplier_id=supplier_id,
            expected_delivery=expected_delivery,
            notes=request.form.get('notes', '')
        )
        
        db.session.add(purchase_order)
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"إنشاء أمر شراء جديد: {purchase_order.po_number}",
            entity_type='PurchaseOrder',
            entity_id=purchase_order.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم إنشاء أمر الشراء بنجاح', 'success')
        return redirect(url_for('suppliers.edit_order', order_id=purchase_order.id))
    
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template('suppliers/add_order.html', suppliers=suppliers)

@suppliers_bp.route('/orders/edit/<order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    """تعديل أمر شراء"""
    order = PurchaseOrder.query.get_or_404(order_id)
    
    if request.method == 'POST':
        # Handle empty date fields
        expected_delivery = request.form.get('expected_delivery', '').strip()
        if expected_delivery:
            try:
                order.expected_delivery = datetime.strptime(expected_delivery, '%Y-%m-%d').date()
            except ValueError:
                order.expected_delivery = None
        else:
            order.expected_delivery = None
        
        order.status = request.form.get('status', order.status)
        order.notes = request.form.get('notes', order.notes)
        
        # حساب إجمالي المبلغ
        total = sum(item.quantity_ordered * item.unit_price for item in order.items)
        order.total_amount = total
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"تعديل أمر شراء: {order.po_number}",
            entity_type='PurchaseOrder',
            entity_id=order.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تحديث أمر الشراء بنجاح', 'success')
        return redirect(url_for('suppliers.orders'))
    
    items = Item.query.filter_by(is_active=True).all()
    return render_template('suppliers/edit_order.html', order=order, items=items)

@suppliers_bp.route('/orders/<order_id>/add-item', methods=['POST'])
@login_required
def add_order_item(order_id):
    """إضافة عنصر لأمر شراء"""
    order = PurchaseOrder.query.get_or_404(order_id)
    
    item_id = request.form.get('item_id', '')
    quantity = request.form.get('quantity', 0)
    unit_price = request.form.get('unit_price', 0)
    
    try:
        quantity = float(quantity)
        unit_price = float(unit_price)
        
        if quantity <= 0 or unit_price < 0:
            flash('الكمية والسعر يجب أن تكون قيم موجبة', 'warning')
            return redirect(url_for('suppliers.edit_order', order_id=order_id))
        
        item = Item.query.get_or_404(item_id)
        
        # التحقق من عدم وجود العنصر بالفعل
        existing_item = PurchaseOrderItem.query.filter_by(
            purchase_order_id=order_id,
            item_id=item_id
        ).first()
        
        if existing_item:
            flash('هذا الصنف موجود بالفعل في أمر الشراء', 'warning')
            return redirect(url_for('suppliers.edit_order', order_id=order_id))
        
        order_item = PurchaseOrderItem(
            purchase_order_id=order_id,
            item_id=item_id,
            quantity_ordered=quantity,
            unit_price=unit_price
        )
        
        db.session.add(order_item)
        db.session.commit()
        
        # حساب إجمالي المبلغ بعد الإضافة والتأكد من التحديث
        # إعادة تحميل العلاقة للحصول على القائمة المحدثة
        db.session.refresh(order)
        total = sum(i.quantity_ordered * i.unit_price for i in order.items)
        order.total_amount = total
        db.session.commit()
        
        flash(f'تم إضافة {item.name} بنجاح', 'success')
        
    except ValueError:
        flash('الكمية والسعر يجب أن تكون أرقام صحيحة', 'danger')
    
    return redirect(url_for('suppliers.edit_order', order_id=order_id))

@suppliers_bp.route('/orders/<order_id>/remove-item/<item_id>', methods=['POST'])
@login_required
def remove_order_item(order_id, item_id):
    """حذف عنصر من أمر شراء"""
    order = PurchaseOrder.query.get_or_404(order_id)
    
    order_item = PurchaseOrderItem.query.filter_by(
        purchase_order_id=order_id,
        item_id=item_id
    ).first_or_404()
    
    item_name = order_item.item.name if order_item.item else 'العنصر'
    
    db.session.delete(order_item)
    db.session.commit()
    
    # حساب إجمالي المبلغ الجديد بعد الحذف
    db.session.refresh(order)
    total = sum(i.quantity_ordered * i.unit_price for i in order.items)
    order.total_amount = total
    db.session.commit()
    
    flash(f'تم حذف {item_name} من الأمر', 'success')
    return redirect(url_for('suppliers.edit_order', order_id=order_id))

@suppliers_bp.route('/orders/<order_id>/invoice')
@login_required
def invoice(order_id):
    """عرض فاتورة أمر الشراء"""
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # الحصول على معلومات المؤسسة
    from models import OrganizationSettings
    org_settings = OrganizationSettings.query.first()
    
    # تنسيق التاريخ والوقت الحالي
    print_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('suppliers/invoice.html', order=order, org_settings=org_settings, print_datetime=print_datetime)