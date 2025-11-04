# 🚀 دليل البدء السريع - نظام الصلاحيات

## الاستخدام السريع

### 1️⃣ فحص الصلاحيات في المسارات (Routes)

```python
from flask import Flask, redirect, url_for, flash
from flask_login import login_required, current_user

@app.route('/inventory/items')
@login_required
def view_items():
    # فحص صلاحية واحدة
    if not current_user.has_granular_permission('inventory_view'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # ... باقي الكود
    return render_template('inventory/items.html')

@app.route('/inventory/items/add', methods=['POST'])
@login_required
def add_item():
    # فحص عدة صلاحيات
    if not (current_user.has_granular_permission('inventory_add') or 
            current_user.has_granular_permission('inventory_edit')):
        flash('ليس لديك صلاحية لإضافة أصناف', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # ... باقي الكود
```

### 2️⃣ فحص الصلاحيات في القوالب (Jinja2 Templates)

```html
<!-- إخفاء/إظهار زر بناءً على الصلاحية -->
{% if has_permission('inventory_add') %}
    <a href="{{ url_for('inventory.add_item') }}" class="btn btn-primary">
        <i class="fas fa-plus"></i> إضافة صنف جديد
    </a>
{% endif %}

<!-- عرض جزء من الصفحة بناءً على الصلاحية -->
{% if has_permission('inventory_delete') %}
    <td>
        <a href="#" class="btn btn-sm btn-danger">
            <i class="fas fa-trash"></i> حذف
        </a>
    </td>
{% endif %}

<!-- استخدام متقدم -->
<table class="table">
    <thead>
        <tr>
            <th>الاسم</th>
            <th>الكمية</th>
            {% if has_permission('inventory_edit') or has_permission('inventory_delete') %}
                <th>الإجراءات</th>
            {% endif %}
        </tr>
    </thead>
    <tbody>
        {% for item in items %}
        <tr>
            <td>{{ item.name }}</td>
            <td>{{ item.quantity }}</td>
            {% if has_permission('inventory_edit') or has_permission('inventory_delete') %}
                <td>
                    {% if has_permission('inventory_edit') %}
                        <a href="{{ url_for('inventory.edit_item', id=item.id) }}" 
                           class="btn btn-sm btn-warning">تعديل</a>
                    {% endif %}
                    {% if has_permission('inventory_delete') %}
                        <form method="POST" action="{{ url_for('inventory.delete_item', id=item.id) }}" 
                              style="display:inline;">
                            <button type="submit" class="btn btn-sm btn-danger"
                                    onclick="return confirm('هل أنت متأكد؟')">حذف</button>
                        </form>
                    {% endif %}
                </td>
            {% endif %}
        </tr>
        {% endfor %}
    </tbody>
</table>
```

## قائمة الصلاحيات المتاحة

### لوحة التحكم (Dashboard)
- `dashboard_view` - عرض لوحة التحكم

### إدارة المخزون (Inventory)
- `inventory_view` - عرض قائمة الأصناف
- `inventory_add` - إضافة صنف جديد
- `inventory_edit` - تعديل الأصناف
- `inventory_delete` - حذف الأصناف
- `inventory_export` - تصدير البيانات

### إدارة التصنيفات (Categories)
- `categories_view` - عرض التصنيفات
- `categories_add` - إضافة تصنيف جديد
- `categories_edit` - تعديل التصنيفات
- `categories_delete` - حذف التصنيفات

### إدارة العمليات (Transactions)
- `transactions_view` - عرض العمليات
- `transactions_add` - تسجيل عملية جديدة
- `transactions_edit` - تعديل العمليات
- `transactions_delete` - حذف العمليات

### إدارة الموردين (Suppliers)
- `suppliers_view` - عرض قائمة الموردين
- `suppliers_add` - إضافة مورد جديد
- `suppliers_edit` - تعديل بيانات الموردين
- `suppliers_delete` - حذف الموردين
- `suppliers_orders` - إدارة أوامر الشراء

### إدارة الأصول (Equipment)
- `equipment_view` - عرض الأصول
- `equipment_add` - تسجيل أصل جديد
- `equipment_edit` - تعديل الأصول
- `equipment_delete` - حذف الأصول
- `equipment_issues` - إدارة المشاكل المسجلة

### إدارة المطعم (Restaurant)
- `recipes_view` - عرض الوصفات
- `recipes_add` - إضافة وصفة جديدة
- `recipes_edit` - تعديل الوصفات
- `recipes_delete` - حذف الوصفات
- `meals_view` - عرض الوجبات اليومية
- `meals_add` - تسجيل وجبة جديدة
- `meals_edit` - تعديل الوجبات
- `meals_delete` - حذف الوجبات

### التقارير (Reports)
- `reports_inventory` - تقرير حركة المخزون
- `reports_low_stock` - تقرير الأصناف منخفضة المخزون
- `reports_equipment` - تقرير الأصول
- `reports_meals` - تقرير استهلاك الوجبات
- `reports_print` - طباعة التقارير
- `reports_export` - تصدير التقارير

### إدارة النظام (Admin)
- `users_view` - عرض المستخدمين
- `users_add` - إضافة مستخدم جديد
- `users_edit` - تعديل المستخدمين
- `users_delete` - حذف المستخدمين
- `permissions_manage` - إدارة الصلاحيات
- `activity_logs` - عرض سجل النشاط
- `settings` - إعدادات المؤسسة

## أمثلة عملية

### مثال 1: حماية صفحة العرض

```python
@app.route('/inventory/items')
@login_required
def list_items():
    if not current_user.has_granular_permission('inventory_view'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    items = Item.query.all()
    return render_template('inventory/items.html', items=items)
```

### مثال 2: حماية عملية الإضافة

```python
@app.route('/inventory/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if not current_user.has_granular_permission('inventory_add'):
        flash('ليس لديك صلاحية لإضافة أصناف', 'danger')
        return redirect(url_for('inventory.list_items'))
    
    if request.method == 'POST':
        # معالجة النموذج
        item = Item(...)
        db.session.add(item)
        db.session.commit()
        flash('تم إضافة الصنف بنجاح', 'success')
        return redirect(url_for('inventory.list_items'))
    
    return render_template('inventory/add_item.html')
```

### مثال 3: إخفاء الأزرار في القالب

```html
<div class="table-responsive">
    <table class="table">
        <tbody>
        {% for item in items %}
            <tr>
                <td>{{ item.name }}</td>
                <td>
                    {% if has_permission('inventory_view') %}
                        <a href="{{ url_for('inventory.view_item', id=item.id) }}" 
                           class="btn btn-sm btn-info">
                            <i class="fas fa-eye"></i> عرض
                        </a>
                    {% endif %}
                    
                    {% if has_permission('inventory_edit') %}
                        <a href="{{ url_for('inventory.edit_item', id=item.id) }}" 
                           class="btn btn-sm btn-warning">
                            <i class="fas fa-edit"></i> تعديل
                        </a>
                    {% endif %}
                    
                    {% if has_permission('inventory_delete') %}
                        <form method="POST" 
                              action="{{ url_for('inventory.delete_item', id=item.id) }}" 
                              style="display:inline;">
                            <button type="submit" class="btn btn-sm btn-danger"
                                    onclick="return confirm('حذف هذا الصنف؟')">
                                <i class="fas fa-trash"></i> حذف
                            </button>
                        </form>
                    {% endif %}
                </td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
</div>
```

### مثال 4: تحكم متقدم مع أدوار

```python
@app.route('/reports/inventory')
@login_required
def inventory_report():
    # تحقق من أي من الصلاحيات
    has_access = any([
        current_user.has_granular_permission('reports_inventory'),
        current_user.has_granular_permission('admin'),
        current_user.role == 'admin'  # أيضاً دعم الأدوار القديمة
    ])
    
    if not has_access:
        flash('ليس لديك صلاحية للوصول إلى التقارير', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # عرض التقرير
    return render_template('reports/inventory.html')
```

## نصائح وأفضليات 💡

### ✅ افعل:
```python
# تحقق من الصلاحيات في المسارات (المهم!)
if not current_user.has_granular_permission('inventory_add'):
    return redirect(url_for('dashboard.index'))
```

```html
<!-- استخدم has_permission في القوالب -->
{% if has_permission('inventory_add') %}
    <button>إضافة</button>
{% endif %}
```

### ❌ لا تفعل:
```python
# لا تعتمد على الفحص في الواجهة الأمامية فقط
# الخادم يجب أن يفحص دائماً
```

```html
<!-- لا تخفِ فقط الزر -->
<!-- المستخدم الماهر يمكنه تجاوز هذا -->
<button>إضافة</button>
```

## إضافة صلاحيات جديدة

لإضافة صلاحية جديدة، عدّل `permissions_config.py`:

```python
PERMISSIONS = {
    'inventory': {
        'name': 'إدارة المخزون',
        'permissions': {
            'inventory_view': 'عرض قائمة الأصناف',
            'inventory_add': 'إضافة صنف جديد',
            'inventory_print': 'طباعة الأصناف',  # ← صلاحية جديدة
        }
    },
}
```

ثم استخدمها في المسارات:
```python
if not current_user.has_granular_permission('inventory_print'):
    return redirect(url_for('dashboard.index'))
```

## استكشاف الأخطاء

### المستخدم يرى الصلاحيات لكن لا يمكنه الوصول
```python
# تأكد من فحص الصلاحيات في المسار
if not current_user.has_granular_permission('inventory_view'):
    flash('ليس لديك صلاحية', 'danger')
    return redirect(...)
```

### الصلاحيات لم تُحفظ
```python
# تأكد من تشغيل init_db.py
# وأن form data صحيحة (perm_XXX)
```

### has_permission لا تعمل في القوالب
```python
# تأكد من تحديث app.py بـ context processor
@app.context_processor
def inject_org_settings():
    ...
    return {
        'has_permission': has_permission,
    }
```

---

**للمزيد من المعلومات، انظر `PERMISSIONS_SYSTEM.md`**