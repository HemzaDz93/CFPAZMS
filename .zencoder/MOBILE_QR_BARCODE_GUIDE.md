# 📱 دليل تطبيق الموبايل و QR/Barcode

## نظرة عامة
تم إضافة تطبيق موبايل متقدم (PWA) مع دعم كامل لـ QR و Barcode للأصول، مع إمكانية العمل بدون إنترنت والمزامنة التلقائية.

---

## ✨ الميزات المضافة

### 1. **تطبيق الموبايل (PWA)**
- تطبيق ويب تقدمي (Progressive Web App)
- يعمل على جميع الأجهزة (Android, iOS, Windows)
- قابل للتثبيت من المتصفح
- واجهة سهلة الاستخدام مخصصة للموبايل
- دعم كامل للعربية (RTL)

#### المميزات:
- 🏠 **لوحة التحكم**: عرض الإحصائيات والمسحات الأخيرة
- 📷 **المسح الذكي**: مسح QR و Barcode من الكاميرا
- 📋 **إدارة الأصول**: عرض جميع الأصول مع التفاصيل
- 🔔 **الإشعارات**: تلقي تنبيهات فورية
- ⚙️ **الإعدادات**: إدارة الجهاز والتخزين

### 2. **دعم QR Code**
#### التوليد التلقائي:
- توليد QR code فريد لكل أصل
- يحتوي على معلومات: `asset_id`, `asset_code`, `serial_number`, `timestamp`
- حفظ تلقائي في المسار: `/uploads/qrcodes/`

#### المسح:
- مسح QR من الكاميرا مباشرة
- فك تشفير البيانات تلقائياً
- تتبع سجل المسحات
- دعم العمل بدون إنترنت

#### API Endpoints:
```
POST   /mobile/asset/<asset_id>/generate-qr      - توليد QR code
GET    /mobile/asset/<asset_id>/qr.png           - عرض صورة QR
POST   /mobile/scan                                - مسح QR/Barcode
```

### 3. **دعم Barcode**
#### التوليد:
- توليد barcode بتنسيقات متعددة: `code128`, `ean13`, `upca`
- رابط مباشر لكل أصل
- حفظ تلقائي

#### المسح:
- مسح من الكاميرا
- إدخال يدوي للرموز
- تتبع كامل للعمليات

#### API Endpoints:
```
POST   /mobile/asset/<asset_id>/generate-barcode  - توليد Barcode
GET    /mobile/asset/<asset_id>/barcode.png       - عرض صورة Barcode
```

### 4. **سجل المسحات (Asset Scan Log)**
- تتبع كل مسحة مع:
  - نوع المسح (QR/Barcode)
  - الإجراء (check_in, check_out, inventory, maintenance)
  - الموقع (GPS/Manual)
  - ملاحظات المستخدم
  - معلومات الجهاز

#### API:
```
GET    /mobile/asset/<asset_id>/scan-history     - سجل المسحات
```

### 5. **العمل بدون إنترنت (Offline)**
#### الميزات:
- تخزين مؤقت ذكي للبيانات (Cache)
- حفظ المسحات محلياً في IndexedDB
- مزامنة تلقائية عند استعادة الاتصال
- Service Worker متقدم

#### البيانات المحفوظة:
- الأصول والبيانات الأساسية
- المسحات والعمليات
- الإشعارات

#### API:
```
POST   /mobile/sync/push                          - مزامنة البيانات للخادم
GET    /mobile/sync/pull                          - جلب البيانات من الخادم
```

### 6. **إدارة الأجهزة (Mobile Devices)**
#### التسجيل:
- تسجيل أجهزة متعددة لنفس المستخدم
- حفظ معلومات الجهاز والنظام
- توليد معرف فريد للجهاز

#### الميزات:
- تتبع آخر نشاط
- دعم Firebase Cloud Messaging (FCM)
- إدارة الإشعارات حسب الجهاز

#### API:
```
POST   /mobile/device/register                    - تسجيل جهاز جديد
GET    /mobile/device/list                        - قائمة الأجهزة
```

### 7. **الإشعارات المحسّنة**
#### أنواع الإشعارات:
- 📡 **Scan**: إشعارات المسح
- ⚠️ **Alert**: تنبيهات النظام
- ✅ **Approval**: الموافقات المعلقة
- 📊 **Inventory**: تنبيهات المخزون

#### API:
```
GET    /mobile/notifications                      - قائمة الإشعارات
POST   /mobile/notifications/<id>/read             - وضع علامة كمقروء
```

---

## 🔧 الهياكل والنماذج

### AssetRegistration (محسّن)
```python
# الحقول الجديدة:
qr_code: LargeBinary              # صورة QR بصيغة ثنائية
qr_code_path: String              # مسار QR code
barcode_code: String              # رمز Barcode
barcode_format: String            # تنسيق الـ Barcode (code128, ean13, etc)
barcode_generated: Boolean        # هل تم توليد الـ Barcode

# العلاقات الجديدة:
scan_logs: [AssetScanLog]        # سجل جميع المسحات
```

### AssetScanLog (نموذج جديد)
```python
id: String(UUID)
asset_id: String                  # ربط الأصل
user_id: String                   # المستخدم الذي قام بالمسح
scan_type: String                 # qr / barcode
scan_location: String             # الموقع (GPS/Manual)
action: String                    # check_in/check_out/inventory/maintenance
notes: Text                       # ملاحظات
scanned_at: DateTime             # وقت المسح
device_info: String              # معلومات الجهاز
```

### MobileDevice (نموذج جديد)
```python
id: String(UUID)
user_id: String                  # المستخدم
device_id: String                # معرف فريد للجهاز
device_name: String              # اسم الجهاز (iPhone 14, Samsung A52, etc)
device_type: String              # ios/android/web
os_version: String               # إصدار النظام
app_version: String              # إصدار التطبيق
fcm_token: String                # Firebase Token
push_enabled: Boolean            # هل الإشعارات مفعلة
last_active: DateTime            # آخر نشاط
```

### MobileNotification (نموذج جديد)
```python
id: String(UUID)
device_id: String                # الجهاز
title: String                    # عنوان الإشعار
message: Text                    # محتوى الإشعار
notification_type: String        # scan/alert/approval/inventory
related_entity_type: String      # نوع الكيان المتعلق (Asset, Item, etc)
related_entity_id: String        # معرف الكيان
data: JSON                       # بيانات إضافية
is_read: Boolean
is_sent: Boolean
sent_at: DateTime
read_at: DateTime
```

### OfflineData (نموذج جديد)
```python
id: String(UUID)
user_id: String                  # المستخدم
device_id: String                # الجهاز
data_type: String                # asset/item/location
entity_id: String                # معرف الكيان
data_snapshot: JSON              # لقطة من البيانات
last_synced: DateTime
is_synced: Boolean
```

### QRCodeMapping (نموذج جديد)
```python
id: String(UUID)
qr_value: String                 # بيانات QR الفريدة
entity_type: String              # asset/item/location
entity_id: String                # معرف الكيان
is_active: Boolean
scans_count: Integer             # عدد المسحات
created_at: DateTime
last_scanned: DateTime
```

---

## 📡 API Reference

### Device Management
```
POST /mobile/device/register
Body: {
  device_id: "unique-device-id",
  device_name: "iPhone 14 Pro",
  device_type: "ios",
  os_version: "17.0",
  app_version: "1.0.0",
  fcm_token: "token..."
}
Response: { success: true, device_id: "..." }

GET /mobile/device/list
Response: {
  success: true,
  devices: [
    { id, device_id, device_name, device_type, ... }
  ]
}
```

### QR Code Operations
```
POST /mobile/asset/:asset_id/generate-qr
Response: { success: true, qr_path: "/uploads/qrcodes/..." }

GET /mobile/asset/:asset_id/qr.png
Response: PNG Image

POST /mobile/asset/:asset_id/generate-barcode
Body: { format: "code128" }
Response: { success: true, barcode_path: "/uploads/barcodes/..." }

GET /mobile/asset/:asset_id/barcode.png
Response: PNG Image
```

### Scanning
```
POST /mobile/scan
Body: {
  scan_data: "asset-qr-data-or-barcode",
  scan_type: "qr",
  action: "check_in",
  scan_location: "12.34, 56.78",
  device_id: "device-id",
  notes: "..."
}
Response: {
  success: true,
  asset: { id, asset_code, serial_number, status, ... },
  scan_log_id: "..."
}

GET /mobile/asset/:asset_id/scan-history?page=1&per_page=20
Response: {
  success: true,
  scans: [...],
  total: 50,
  pages: 3
}
```

### Data Synchronization
```
POST /mobile/sync/push
Body: {
  device_id: "...",
  offline_data: [
    { data_type: "asset_scan", entity_id: "...", changes: {} }
  ]
}
Response: { success: true, synced_count: 5 }

GET /mobile/sync/pull?data_types=assets,items,locations
Response: {
  success: true,
  sync_data: {
    assets: [...],
    items: [...],
    locations: [...]
  },
  timestamp: "2024-01-01T00:00:00Z"
}
```

### Dashboard & Notifications
```
GET /mobile/dashboard/stats
Response: {
  success: true,
  stats: {
    total_assets: 100,
    in_service_assets: 85,
    defective_assets: 10,
    unread_notifications: 3
  },
  recent_scans: [...]
}

GET /mobile/notifications
Response: {
  success: true,
  notifications: [
    { id, title, message, notification_type, is_read, ... }
  ]
}

POST /mobile/notifications/:id/read
Response: { success: true }
```

---

## 🚀 كيفية الاستخدام

### للمستخدم النهائي:

#### 1. **الوصول للتطبيق:**
```
اذهب إلى: https://your-domain.com/mobile/app
```

#### 2. **تثبيت التطبيق (PWA):**
- على Android: اضغط "إضافة إلى الشاشة الرئيسية" (Add to Home Screen)
- على iOS: اضغط المشاركة ثم "إضافة إلى الشاشة الرئيسية"
- على سطح المكتب: اضغط "تثبيت" في المتصفح

#### 3. **مسح QR/Barcode:**
1. افتح التطبيق وانتقل إلى تبويب "مسح"
2. اختر نوع المسح (QR أو Barcode)
3. وجّه الكاميرا نحو الرمز
4. سيتم المسح تلقائياً
5. اختر الإجراء (فحص الدخول/الخروج/جرد/صيانة)
6. أضف موقع (يدوي أو GPS)
7. أضف ملاحظات إن لزم
8. تم! سيتم الحفظ حتى بدون إنترنت

#### 4. **عرض الأصول:**
- انتقل إلى تبويب "الأصول"
- ابحث عن أصل محدد
- انقر للرؤية التفاصيل

### للمطورين:

#### إضافة QR/Barcode للأصل الموجود:
```bash
# الوصول للخادم
curl -X POST http://localhost:5000/mobile/asset/ASSET_ID/generate-qr \
  -H "Authorization: Bearer TOKEN"

# أو للـ Barcode
curl -X POST http://localhost:5000/mobile/asset/ASSET_ID/generate-barcode \
  -H "Authorization: Bearer TOKEN" \
  -d '{"format": "code128"}'
```

#### تسجيل جهاز جديد برمجياً:
```javascript
const response = await fetch('/mobile/device/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    device_id: 'unique-id-' + Date.now(),
    device_name: 'My Device',
    device_type: 'web',
    app_version: '1.0.0'
  })
});
```

---

## 🛠️ التثبيت والإعداد

### 1. **تثبيت المتطلبات:**
```bash
pip install -r requirements.txt
```

المتطلبات الجديدة:
- `python-barcode` - توليد Barcode
- `qrcode` - توليد QR (مثبت بالفعل)
- `firebase-admin` - الإشعارات (اختياري)
- `flask-cors` - CORS Support

### 2. **إنشاء قاعدة البيانات:**
```bash
flask db init      # إذا كنت تستخدم Flask-Migrate
flask db migrate
flask db upgrade
# أو
python
>>> from app import db, create_app
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
```

### 3. **تشغيل الخادم:**
```bash
python app.py
# أو
flask run
```

### 4. **الوصول للتطبيق:**
```
http://localhost:5000/mobile/app
```

---

## 📋 ملاحظات مهمة

### الأداء:
- ✅ Service Worker يحسّن الأداء تلقائياً
- ✅ تخزين مؤقت ذكي للصور والموارد
- ✅ ضغط البيانات تلقائي

### الأمان:
- ✅ جميع المسحات محمية بـ login_required
- ✅ التشفير للبيانات الحساسة (HTTPS)
- ✅ معرف جهاز فريد لكل جهاز

### التوافقية:
- ✅ Chrome 40+
- ✅ Firefox 35+
- ✅ Safari 11+
- ✅ Edge 15+
- ✅ جميع متصفحات Android

### الصيانة:
- تنظيف سجلات المسحات القديمة: إضافة Cron Job
- مزامنة البيانات: تلقائية عند استعادة الإنترنت
- التحديثات التلقائية: Service Worker

---

## 🐛 استكشاف الأخطاء

### المشكلة: الكاميرا لا تعمل
- **السبب**: عدم إعطاء الصلاحيات
- **الحل**: اسمح بالوصول للكاميرا من إعدادات المتصفح

### المشكلة: بطء المسح
- **السبب**: جودة الكاميرا منخفضة
- **الحل**: نظّف عدسة الكاميرا، اقترب من الرمز

### المشكلة: عدم المزامنة بدون إنترنت
- **السبب**: IndexedDB ممتلئة
- **الحل**: امسح البيانات المحفوظة من الإعدادات

---

## 📚 موارد إضافية

### توليد رموز QR و Barcode بدون التطبيق:
```python
import qrcode
import barcode

# QR Code
qr = qrcode.QRCode()
qr.add_data("asset_12345")
qr.make()
img = qr.make_image()
img.save("qr_code.png")

# Barcode
ean = barcode.get_barcode_class('code128')
ean_instance = ean('123456789')
ean_instance.save('barcode')
```

### طباعة الرموز:
```html
<button onclick="window.print()">طباعة</button>
```

---

## 🎯 الخطوات التالية

1. ✅ إضافة دعم Firebase للإشعارات
2. ✅ تطوير تطبيق Native (React Native / Flutter)
3. ✅ إضافة تقارير متقدمة
4. ✅ دعم الموقع الجغرافي المتقدم
5. ✅ تكامل مع أنظمة الدفع

---

**تم التحديث في:** 2024
**الإصدار:** 1.0.0