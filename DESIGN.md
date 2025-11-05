## تصميم معماري وتفصيلي لنظام CfpaZMS

هذا المستند يكمل الوثائق الحالية ويقدّم تصميمًا مفصّلًا باللغة العربية يحتوي على: مكونات النظام، مخططات (Mermaid)، عقود API رئيسية، بنية قاعدة البيانات المتعلقة بالصلاحيات، خطوات هجرة مقترحة، واقتراحات تنفيذية.

---

## 1. ملخص النظام

- نوع التطبيق: تطبيق ويب مبني بـ Flask (Python) لإدارة المخزون، الأصول، المطعم، والموارد البشرية بصلاحيات حبيبية (Granular Permissions).
- قاعدة البيانات: SQL (حاليًا SQLite في التطوير؛ قابل للتغيير إلى PostgreSQL/MySQL في الإنتاج).
- مكونات رئيسية:
  - خادم Flask + Blueprints (`routes/*.py`).
  - ORM: SQLAlchemy (`models.py`).
  - نظام تسجيل الدخول: Flask-Login.
  - ملفات القوالب: Jinja2 (`templates/`).
  - ملف تعريف الصلاحيات: `permissions_config.py`.
  - نموذج صلاحيات المستخدم: `UserPermission` في `models.py`.

## 2. مخطط المكونات (Mermaid)

```mermaid
graph LR
  Browser["مستخدم / واجهة أمامية (Browser)"] -->|HTTP| Flask["Flask App (routes/*)"]
  Flask -->|ORM| DB[("قاعدة البيانات (SQL)")]
  Flask --> Templates["Jinja2 Templates"]
  Flask -->|Context Processor| Permissions["permissions_config.py"]
  Flask -->|Login| Auth["Flask-Login"]
  DB -->|Models| Models["models.py (User, UserPermission, ...)"]
  subgraph Services
    Notifications["خدمة الإشعارات"]
    Exports["خدمة التصدير (PDF/Excel)"]
  end
  Flask --> Services

  click Database
```

> ملاحظة: يمكنك عرض مخططات Mermaid مباشرة على GitHub أو أدوات تدعم Mermaid لعرض الرسوم التوضيحية.

## 3. تدفق صلاحيات المستخدم (مختصر)

1. المدير يحدد الصلاحيات عند إنشاء/تعديل مستخدم عبر واجهة الإدارة.
2. عند حفظ النموذج، تُستدعى دالة `_update_user_permissions()` في `routes/admin.py` (مذكورة في الوثائق) والتي تحفظ سجل `UserPermission` لكل مفتاح صلاحية.
3. عند كل طلب، `current_user.has_granular_permission(permission_key)` يُستخدم لفحص ما إذا كانت الصلاحية مسموحة (Server-side enforcement).
4. في القوالب، `has_permission(permission_key)` المتوفر عبر context processor يعرض/يخفي عناصر الواجهة.

## 4. نموذج قاعدة البيانات — جدول الصلاحيات (مفصّل)

- اسم الجدول: `user_permissions`
- الحقول الأساسية:
  - `id` (UUID/string, PK)
  - `user_id` (FK → `users.id`)
  - `permission_key` (string)
  - `permission_name` (string) — وصف داخل الواجهة
  - `permission_category` (string)
  - `is_allowed` (boolean)
  - `created_at`, `updated_at`

Unique constraint: (`user_id`, `permission_key`)

مثال SQL (مكافئ لما في `models.py`):

```sql
CREATE TABLE user_permissions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  permission_key TEXT NOT NULL,
  permission_name TEXT NOT NULL,
  permission_category TEXT NOT NULL,
  is_allowed BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, permission_key)
);
```

## 5. عقود API المقترحة (Endpoints رئيسية)

ملاحظة: مستندة على ممارسات نومي REST وملاءمة مع `routes/admin.py` الحالي.

- 1) إضافة مستخدم جديد (مع صلاحيات)
  - مسار: POST /admin/users/add (أو API: POST /api/admin/users)
  - وصف: ينشئ مستخدماً ويخزن الصلاحيات المختارة
  - Request (JSON):

```json
{
  "username": "ahmed",
  "email": "ahmed@example.com",
  "first_name": "أحمد",
  "last_name": "علي",
  "password": "secret",
  "role": "warehouse_manager",
  "permissions": ["inventory_view_items", "inventory_add_item"]
}
```

  - Response (201):

```json
{
  "success": true,
  "user_id": "...",
  "message": "تم إنشاء المستخدم"
}
```

- 2) تعديل صلاحيات مستخدم
  - مسار: PUT /admin/users/<user_id>/permissions (أو PATCH)
  - Request (JSON):

```json
{
  "permissions": {
    "inventory_view_items": true,
    "inventory_delete_item": false
  }
}
```

  - Response (200):

```json
{ "success": true, "message": "تم تحديث الصلاحيات" }
```

- 3) استرجاع صلاحيات المستخدم (لتحريك واجهة التعديل)
  - GET /admin/users/<user_id>/permissions
  - Response (200):

```json
{
  "user_id": "...",
  "permissions": {
    "inventory_view_items": true,
    "inventory_add_item": false
  }
}
```

- 4) API الإشعارات (موجود بالفعل)
  - GET /api/notifications
  - ترد بإجمالي الإشعارات وعدد غير المقروءة (كما في `routes/__init__.py`).

## 6. أمثلة تنفيذية — تحديث صلاحيات (مقترح الدالة `_update_user_permissions`)

مبدأ العمل:
1. استقبل قائمة الصلاحيات المرغوبة من العميل.
2. قم بمقارنة مع الصلاحيات الحالية في DB.
3. حدّث سجلات `UserPermission`: أضف أو حدّث `is_allowed`، واحذف السجلات غير المرغوب بها إذا لزم.

خُطوط تنفيذ سريعة (غير ملزمة):

```python
def update_user_permissions(user_id, permissions_dict):
    # permissions_dict: { 'perm_key': True/False }
    existing = {p.permission_key: p for p in UserPermission.query.filter_by(user_id=user_id)}
    for key, allowed in permissions_dict.items():
        if key in existing:
            existing[key].is_allowed = bool(allowed)
        else:
            meta = get_all_permissions_flat().get(key, {})
            new_p = UserPermission(
                user_id=user_id,
                permission_key=key,
                permission_name=meta.get('name', key),
                permission_category=meta.get('category', 'custom'),
                is_allowed=bool(allowed)
            )
            db.session.add(new_p)
    db.session.commit()
```

## 7. أمان واعتبارات مهمة

- التأكد من فحص الصلاحيات دائماً على الخادم — لا تعتمد على إخفاء الأزرار في الواجهة فقط.
- حماية نقاط النهاية الإدارية بـ `@login_required` وحقق أن `current_user` لديه صلاحية `admin_manage_permissions` قبل السماح بالتعديل.
- منع CSRF في نماذج HTML (WTF-CSRF) و/أو استخدام رؤوس CSRF للتطبيقات التي تستخدم API.
- قيود على حجم قائمة الصلاحيات: في حال تغيّر PERMISSIONS بشكل متكرر، اجعل `permission_key` ثابتاً ولا تحذف/تعيد استخدام المفاتيح لتفادي تلوث السجلات.

## 8. هجرات قاعدة البيانات (Migration plan)

خيار موصى به: استخدم Alembic لإدارة هجرات قواعد البيانات. خطوات سريعة:

1. تهيئة Alembic ومولّد الهجرات:

```powershell
python -m pip install alembic
alembic init alembic
```

2. إعداد `alembic.ini` و`env.py` لاستخدام SQLAlchemy app metadata (models.db.metadata).
3. إنشاء هجرة تقوم بإنشاء جدول `user_permissions` أو تعديلها إن كانت موجودة.
4. `alembic revision --autogenerate -m "create user_permissions"`
5. `alembic upgrade head`

بديل مباشر وخفيف (غير موصى للإنتاج): تنفيذ SQL مباشر داخل `app.cli` كما في `init_db()`.

## 9. اختبارات مقترحة (مستوى الوحدة)

- اختبار `User.has_granular_permission`:
  - إعداد مستخدم مع صلاحية محددة في `user_permissions`, تأكد أن الدالة ترجع True.
  - حالة عدم وجود الصلاحية تُعيد False.

- اختبار API إضافة/تعديل المستخدمين (مع صلاحيات):
  - تحقق من أن بعد POST المستخدم وحقول `user_permissions` صحيحة.

## 10. التشغيل المحلي والاختبار (PowerShell)

1) إنشاء بيئة افتراضية وتثبيت المتطلبات:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate
pip install -r requirements.txt
```

2) تهيئة قاعدة البيانات (كما في `app.py`):

```powershell
set FLASK_APP=app.py
set FLASK_ENV=development
flask init_db
```

3) تشغيل السيرفر:

```powershell
flask run
```

4) تشغيل الاختبارات (إن وُجدت):

```powershell
pytest -q
```

## 11. اقتراحات لتحسينات مستقبلية

- إضافة طبقة Roles-to-Permissions (مجموعات صلاحيات) لتسهيل إدارة المستخدمين: حفظ جداول `roles`, `role_permissions`, `user_roles`.
- إضافة واجهة إدارية لتحميل/export مجموعة صلاحيات (JSON) وواجهات API لإدارة البرامج النصية للترحيل.
- إضافة سجلات تدقيق تفصيلية عند تغيير صلاحيات المستخدم في `ActivityLog` أو `DetailedAuditLog`.
- تحسين أداء استعلام الصلاحيات باستخدام caching بسيط (مثلاً Redis) أو حفظ قائمة الصلاحيات المسموحة في حقل JSON داخل جدول `users` مُحدَّث عند كل تغيير صلاحيات.

## 12. الخلاصة وما أنجزته هنا

- أنشأت وصف تصميمي مفصّل بالعربية قابل للاستخدام كمستند مرجعي للتنفيذ.
- يتضمن المستند مخططات Mermaid، عقود API، مثال دوال تحديث الصلاحيات، خطة هجرة باستخدام Alembic، ونقاط أمان واختبارات.

إذا رغبت، أستطيع الآن:
- تحديث `ARCHITECTURE_DIAGRAM.md` لدمج مخطط Mermaid أعلاه.
- إنشاء هجرة Alembic فعلية أو سكربت SQL لإنشاء `user_permissions`.
- إضافة اختبار PyTest صغير لـ `has_granular_permission` وتشغيله.

اختر أي من الخطوات الثلاثة لأتابع التنفيذ.
