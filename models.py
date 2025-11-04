from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from enum import Enum
import uuid

db = SQLAlchemy()

# Enums
class UserRole(str, Enum):
    """أدوار المستخدمين"""
    ADMIN = "admin"  # مدير النظام
    DIRECTOR = "director"  # مدير المؤسسة
    WAREHOUSE_MANAGER = "warehouse_manager"  # أمين المخزن
    ACCOUNTANT = "accountant"  # محاسب
    ECONOMIST = "economist"  # مقتصد
    CHEF = "chef"  # الطباخ
    WORKER = "worker"  # عامل/عون
    VIEWER = "viewer"  # مشاهد فقط

class ItemCategory(str, Enum):
    """فئات الأصناف"""
    OFFICE_EQUIPMENT = "office_equipment"  # تجهيزات مكتبية
    ELECTRONIC_EQUIPMENT = "electronic_equipment"  # تجهيزات إلكترونية
    CONSUMABLES = "consumables"  # مواد استهلاكية
    FOOD_ITEMS = "food_items"  # مواد غذائية
    OTHER = "other"  # أخرى

class ItemStatus(str, Enum):
    """حالة الأصل"""
    IN_SERVICE = "in_service"  # في الخدمة
    DEFECTIVE = "defective"  # معطل
    LOST = "lost"  # مفقود
    RETURNED = "returned"  # مسترجع

class TransactionType(str, Enum):
    """نوع العملية"""
    PURCHASE = "purchase"  # شراء
    ISSUE = "issue"  # إصدار/إخراج
    RETURN = "return"  # إرجاع
    TRANSFER = "transfer"  # تحويل
    ADJUSTMENT = "adjustment"  # تسوية

# ==================== Models ====================

class OrganizationSettings(db.Model):
    """إعدادات المؤسسة"""
    __tablename__ = 'organization_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    ministry_name = db.Column(db.String(255), nullable=False, default="وزارة")
    ministry_name_en = db.Column(db.String(255), nullable=True)
    
    directorate_name = db.Column(db.String(255), nullable=False, default="المديرية")
    directorate_name_en = db.Column(db.String(255), nullable=True)
    
    institution_name = db.Column(db.String(255), nullable=False, default="المؤسسة")
    institution_name_en = db.Column(db.String(255), nullable=True)
    
    institution_code = db.Column(db.String(50), unique=True, nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)  # الرقم الجبائي
    
    logo_path = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    
    # Restaurant Settings
    meal_cost_per_unit = db.Column(db.Float, nullable=False, default=2.5)  # سعر الوجبة الواحدة
    meal_alert_threshold = db.Column(db.Float, nullable=False, default=500.0)  # عتبة التنبيه
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(255), nullable=True)  # اسم من قام بالتحديث
    
    def __repr__(self):
        return f'<OrganizationSettings {self.institution_name}>'
    
    def get_header_text(self):
        """الحصول على نص رأس الوثيقة"""
        return f"{self.ministry_name}\n{self.directorate_name}\n{self.institution_name}"


class User(UserMixin, db.Model):
    """نموذج المستخدم"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    
    role = db.Column(db.String(50), nullable=False, default=UserRole.WORKER)
    department = db.Column(db.String(100), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    rank = db.Column(db.String(100), nullable=True)  # الرتبة
    
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    issued_items = db.relationship('ItemIssue', backref='issued_to', lazy=True)
    transactions = db.relationship('Transaction', backref='created_by_user', lazy=True)
    user_permissions = db.relationship('UserPermission', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """تعيين كلمة المرور (مشفرة)"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)
    
    def has_granular_permission(self, permission_key):
        """التحقق من صلاحية حبيبية محددة"""
        return UserPermission.query.filter_by(
            user_id=self.id,
            permission_key=permission_key,
            is_allowed=True
        ).first() is not None
    
    def get_all_permissions(self):
        """الحصول على جميع الصلاحيات المسموحة للمستخدم"""
        permissions = UserPermission.query.filter_by(
            user_id=self.id,
            is_allowed=True
        ).all()
        return {p.permission_key for p in permissions}
    
    def has_permission(self, required_role):
        """التحقق من الصلاحيات"""
        role_hierarchy = {
            UserRole.ADMIN: 9,
            UserRole.DIRECTOR: 8,
            UserRole.ACCOUNTANT: 7,
            UserRole.ECONOMIST: 6,
            UserRole.WAREHOUSE_MANAGER: 5,
            UserRole.CHEF: 4,
            UserRole.WORKER: 3,
            UserRole.VIEWER: 1
        }
        user_level = role_hierarchy.get(UserRole(self.role), 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level
    
    def has_granular_permission(self, permission_key):
        """التحقق من صلاحية حبيبية محددة"""
        return UserPermission.query.filter_by(
            user_id=self.id,
            permission_key=permission_key,
            is_allowed=True
        ).first() is not None
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class UserPermission(db.Model):
    """نموذج الصلاحيات المستخدم"""
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    permission_key = db.Column(db.String(100), nullable=False)  # مفتاح الصلاحية
    permission_name = db.Column(db.String(255), nullable=False)  # اسم الصلاحية
    permission_category = db.Column(db.String(100), nullable=False)  # الفئة (inventory, equipment, etc)
    
    is_allowed = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'permission_key', name='unique_user_permission'),)
    
    def __repr__(self):
        return f'<UserPermission {self.user_id}:{self.permission_key}>'


class ItemCategory_Model(db.Model):
    """نموذج تصنيفات الأصناف"""
    __tablename__ = 'item_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_type = db.Column(db.String(50), nullable=False)  # office_equipment, electronic, etc
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('Item', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ItemCategory {self.name}>'


class Item(db.Model):
    """نموذج الأصناف (المواد)"""
    __tablename__ = 'items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    category_id = db.Column(db.Integer, db.ForeignKey('item_categories.id'), nullable=False)
    unit = db.Column(db.String(50), nullable=False)  # قطعة، كغ، لتر، إلخ
    
    quantity_in_stock = db.Column(db.Float, default=0)
    minimum_quantity = db.Column(db.Float, default=0)  # الحد الأدنى للمخزون
    unit_price = db.Column(db.Float, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    transactions = db.relationship('Transaction', backref='item', lazy=True)
    asset_registrations = db.relationship('AssetRegistration', backref='item', lazy=True)
    
    def __repr__(self):
        return f'<Item {self.code}>'
    
    @property
    def is_low_stock(self):
        """التحقق من انخفاض المخزون"""
        return self.quantity_in_stock <= self.minimum_quantity


class Supplier(db.Model):
    """نموذج الموردين"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    tax_id = db.Column(db.String(50), nullable=True)  # الرقم الجبائي
    registration_number = db.Column(db.String(100), nullable=True)
    
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    
    phone = db.Column(db.String(20), nullable=True)
    fax = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    contact_person = db.Column(db.String(255), nullable=True)
    
    bank_details = db.Column(db.Text, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'


class PurchaseOrder(db.Model):
    """نموذج أوامر الشراء"""
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=False)
    
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expected_delivery = db.Column(db.DateTime, nullable=True)
    
    total_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="pending")  # pending, received, partial, cancelled
    
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PurchaseOrder {self.po_number}>'


class PurchaseOrderItem(db.Model):
    """نموذج عناصر أوامر الشراء"""
    __tablename__ = 'purchase_order_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_order_id = db.Column(db.String(36), db.ForeignKey('purchase_orders.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    quantity_ordered = db.Column(db.Float, nullable=False)
    quantity_received = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Float, nullable=False)
    
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<PurchaseOrderItem {self.id}>'


class Transaction(db.Model):
    """نموذج العمليات (حركة المخزون)"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_number = db.Column(db.String(50), unique=True, nullable=False)
    
    transaction_type = db.Column(db.String(50), nullable=False)  # purchase, issue, return, transfer, adjustment
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=True)
    total_value = db.Column(db.Float, nullable=True)
    
    from_location = db.Column(db.String(255), nullable=True)
    to_location = db.Column(db.String(255), nullable=True)
    
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.reference_number}>'


class AssetRegistration(db.Model):
    """نموذج تسجيل الأصول (الممتلكات)"""
    __tablename__ = 'asset_registrations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_code = db.Column(db.String(50), unique=True, nullable=False)
    serial_number = db.Column(db.String(100), nullable=True)
    
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    acquisition_date = db.Column(db.DateTime, nullable=False)
    acquisition_price = db.Column(db.Float, nullable=True)
    
    status = db.Column(db.String(50), default="in_service")  # in_service, defective, lost, returned
    location = db.Column(db.String(255), nullable=True)
    
    # === QR و Barcode Support ===
    qr_code = db.Column(db.LargeBinary, nullable=True)  # QR code image binary
    qr_code_path = db.Column(db.String(255), nullable=True)  # QR code file path
    barcode_code = db.Column(db.String(50), nullable=True)  # Barcode string (same as asset_code or different)
    barcode_format = db.Column(db.String(20), default="code128")  # code128, ean13, upca, etc
    barcode_generated = db.Column(db.Boolean, default=False)  # هل تم توليد الـ Barcode
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    assignments = db.relationship('ItemIssue', backref='asset', lazy=True)
    scan_logs = db.relationship('AssetScanLog', backref='asset', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AssetRegistration {self.asset_code}>'
    
    def get_qr_url(self):
        """الحصول على رابط الـ QR الشامل (للموبايل)"""
        return f"asset-detail/{self.id}"
    
    def get_barcode_value(self):
        """الحصول على قيمة الـ Barcode"""
        return self.barcode_code or self.asset_code


class AssetScanLog(db.Model):
    """نموذج سجل مسح الأصول (QR/Barcode)"""
    __tablename__ = 'asset_scan_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = db.Column(db.String(36), db.ForeignKey('asset_registrations.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    scan_type = db.Column(db.String(20), nullable=False)  # qr, barcode
    scan_location = db.Column(db.String(255), nullable=True)  # GPS coordinates or location name
    
    action = db.Column(db.String(50), nullable=False)  # check_in, check_out, inventory, maintenance
    notes = db.Column(db.Text, nullable=True)
    
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    device_info = db.Column(db.String(255), nullable=True)  # Mobile device info
    
    def __repr__(self):
        return f'<AssetScanLog {self.asset_id}>'


class ItemIssue(db.Model):
    """نموذج تسليم العتاد للموظفين"""
    __tablename__ = 'item_issues'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_number = db.Column(db.String(50), unique=True, nullable=False)
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    asset_id = db.Column(db.String(36), db.ForeignKey('asset_registrations.id'), nullable=False)
    
    issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expected_return_date = db.Column(db.DateTime, nullable=True)
    actual_return_date = db.Column(db.DateTime, nullable=True)
    
    condition_on_issue = db.Column(db.String(255), nullable=True)
    condition_on_return = db.Column(db.String(255), nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ItemIssue {self.issue_number}>'


class Recipe(db.Model):
    """نموذج الوصفات (للمطعم)"""
    __tablename__ = 'recipes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    servings = db.Column(db.Integer, default=1)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Recipe {self.name}>'


class RecipeIngredient(db.Model):
    """نموذج مكونات الوصفة"""
    __tablename__ = 'recipe_ingredients'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipe_id = db.Column(db.String(36), db.ForeignKey('recipes.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<RecipeIngredient {self.id}>'


class MealRecord(db.Model):
    """نموذج سجل الوجبات اليومي"""
    __tablename__ = 'meal_records'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    meal_type = db.Column(db.String(50), nullable=False)  # breakfast, lunch, dinner
    recipe_id = db.Column(db.String(36), db.ForeignKey('recipes.id'), nullable=False)
    servings = db.Column(db.Integer, default=1)
    expected_cost = db.Column(db.Float, nullable=True)  # تكلفة الوجبة المتوقعة
    
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    recipe = db.relationship('Recipe')
    
    def __repr__(self):
        return f'<MealRecord {self.record_date}>'


class ActivityLog(db.Model):
    """نموذج سجل النشاطات"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    
    entity_type = db.Column(db.String(100), nullable=True)  # User, Item, etc
    entity_id = db.Column(db.String(36), nullable=True)
    
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'


# ==================== ADVANCED FEATURES MODELS ====================

# 1. NOTIFICATIONS & ALERTS
class Notification(db.Model):
    """نموذج الإشعارات والتنبيهات"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # low_stock, warranty_expiry, order_pending, etc
    
    entity_type = db.Column(db.String(100), nullable=True)  # Item, Asset, Purchase Order
    entity_id = db.Column(db.String(36), nullable=True)
    
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User')


class Alert(db.Model):
    """نموذج التنبيهات التلقائية"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    alert_type = db.Column(db.String(50), nullable=False)  # low_stock, warranty_expiry, budget_exceeded
    condition = db.Column(db.String(50), nullable=False)  # threshold value
    
    entity_type = db.Column(db.String(100), nullable=False)  # Item, Asset
    entity_id = db.Column(db.String(36), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    notification_channels = db.Column(db.String(255), default='email,dashboard')  # email, sms, dashboard
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 2. WORKFLOW & APPROVALS
class WorkflowApproval(db.Model):
    """نموذج الموافقات والتصاريح"""
    __tablename__ = 'workflow_approvals'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    workflow_type = db.Column(db.String(50), nullable=False)  # purchase_order, expense, high_value_item
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(36), nullable=False)
    
    requested_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    reason = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    requested_by = db.relationship('User', foreign_keys=[requested_by_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])


class WorkflowStep(db.Model):
    """نموذج مراحل سير العمل"""
    __tablename__ = 'workflow_steps'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_approval_id = db.Column(db.String(36), db.ForeignKey('workflow_approvals.id'), nullable=False)
    
    step_order = db.Column(db.Integer, nullable=False)
    approver_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    approver = db.relationship('User')


# 3. API & REST
class APIKey(db.Model):
    """نموذج مفاتيح API"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    key = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    last_used = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User')


# 4. MFA & SECURITY
class UserMFASettings(db.Model):
    """نموذج إعدادات المصادقة متعددة العوامل"""
    __tablename__ = 'user_mfa_settings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_method = db.Column(db.String(50), default='totp')  # totp, sms, email
    
    secret_key = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    
    backup_codes = db.Column(db.Text, nullable=True)  # Comma-separated
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User')


class LoginAttempt(db.Model):
    """نموذج محاولات تسجيل الدخول"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    username = db.Column(db.String(64), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255), nullable=True)
    
    success = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 5. ADVANCED REPORTING
class Report(db.Model):
    """نموذج التقارير المخصصة"""
    __tablename__ = 'reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.String(50), nullable=False)  # inventory, sales, expenses, etc
    
    filters = db.Column(db.Text, nullable=True)  # JSON format
    columns = db.Column(db.Text, nullable=True)  # JSON format
    
    is_scheduled = db.Column(db.Boolean, default=False)
    schedule_frequency = db.Column(db.String(50), nullable=True)  # daily, weekly, monthly
    
    last_generated = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User')


class ReportSchedule(db.Model):
    """نموذج جدولة التقارير"""
    __tablename__ = 'report_schedules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = db.Column(db.String(36), db.ForeignKey('reports.id'), nullable=False)
    
    frequency = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly
    time_of_day = db.Column(db.String(5), nullable=False)  # HH:MM
    email_recipients = db.Column(db.Text, nullable=True)  # Comma-separated emails
    
    is_active = db.Column(db.Boolean, default=True)
    last_sent = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 6. BUDGET & COST TRACKING
class Budget(db.Model):
    """نموذج الميزانيات"""
    __tablename__ = 'budgets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    department = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # Category or item type
    
    fiscal_year = db.Column(db.Integer, nullable=False)
    budget_amount = db.Column(db.Float, nullable=False)
    spent_amount = db.Column(db.Float, default=0)
    
    alert_threshold = db.Column(db.Float, default=80)  # Alert when 80% spent
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BudgetTransaction(db.Model):
    """نموذج معاملات الميزانية"""
    __tablename__ = 'budget_transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    budget_id = db.Column(db.String(36), db.ForeignKey('budgets.id'), nullable=False)
    
    entity_type = db.Column(db.String(100), nullable=False)  # PurchaseOrder, Expense
    entity_id = db.Column(db.String(36), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    budget = db.relationship('Budget')


# 7. BACKUP & RECOVERY
class Backup(db.Model):
    """نموذج النسخ الاحتياطية"""
    __tablename__ = 'backups'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    backup_type = db.Column(db.String(50), nullable=False)  # full, incremental
    storage_location = db.Column(db.String(255), nullable=False)  # local, cloud, etc
    storage_url = db.Column(db.String(512), nullable=True)
    
    file_size = db.Column(db.BigInteger, nullable=True)
    file_hash = db.Column(db.String(255), nullable=True)
    
    is_verified = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)


class BackupSchedule(db.Model):
    """نموذج جدولة النسخ الاحتياطية"""
    __tablename__ = 'backup_schedules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    frequency = db.Column(db.String(50), nullable=False)  # hourly, daily, weekly
    time_of_day = db.Column(db.String(5), nullable=True)  # HH:MM
    
    storage_location = db.Column(db.String(255), nullable=False)
    retention_days = db.Column(db.Integer, default=30)
    
    is_active = db.Column(db.Boolean, default=True)
    last_backup = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 8. ANALYTICS & FORECASTING
class Analytics(db.Model):
    """نموذج التحليلات والإحصائيات"""
    __tablename__ = 'analytics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    metric_name = db.Column(db.String(255), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # count, sum, average, etc
    
    value = db.Column(db.Float, nullable=False)
    
    entity_type = db.Column(db.String(100), nullable=True)
    entity_id = db.Column(db.String(36), nullable=True)
    
    period_date = db.Column(db.Date, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Forecast(db.Model):
    """نموذج التنبؤات"""
    __tablename__ = 'forecasts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    forecast_type = db.Column(db.String(50), nullable=False)  # demand, stock, cost
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(36), nullable=True)
    
    predicted_value = db.Column(db.Float, nullable=False)
    confidence_level = db.Column(db.Float, nullable=False)  # 0-1
    
    forecast_for_date = db.Column(db.Date, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 9. MASTER DATA / REFERENCES
class Branch(db.Model):
    """نموذج الفروع والمواقع"""
    __tablename__ = 'branches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    manager_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Department(db.Model):
    """نموذج الأقسام"""
    __tablename__ = 'departments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    
    manager_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    branch_id = db.Column(db.String(36), db.ForeignKey('branches.id'), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UnitOfMeasure(db.Model):
    """نموذج وحدات القياس"""
    __tablename__ = 'units_of_measure'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    
    category = db.Column(db.String(50), nullable=False)  # weight, volume, length, count
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UnitConversion(db.Model):
    """نموذج تحويلات الوحدات"""
    __tablename__ = 'unit_conversions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    from_unit_id = db.Column(db.String(36), db.ForeignKey('units_of_measure.id'), nullable=False)
    to_unit_id = db.Column(db.String(36), db.ForeignKey('units_of_measure.id'), nullable=False)
    
    conversion_factor = db.Column(db.Float, nullable=False)
    
    from_unit = db.relationship('UnitOfMeasure', foreign_keys=[from_unit_id])
    to_unit = db.relationship('UnitOfMeasure', foreign_keys=[to_unit_id])


# 10. ADVANCED AUDIT TRAIL
class DetailedAuditLog(db.Model):
    """نموذج سجل التدقيق التفصيلي"""
    __tablename__ = 'detailed_audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(36), nullable=False)
    
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW
    
    old_values = db.Column(db.Text, nullable=True)  # JSON format
    new_values = db.Column(db.Text, nullable=True)  # JSON format
    
    change_summary = db.Column(db.Text, nullable=True)
    
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')


# 11. ADVANCED SEARCH & FILTERING
class SavedFilter(db.Model):
    """نموذج التصفية المحفوظة"""
    __tablename__ = 'saved_filters'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(100), nullable=False)  # Item, Supplier, etc
    filter_criteria = db.Column(db.Text, nullable=False)  # JSON format
    
    is_default = db.Column(db.Boolean, default=False)
    is_shared = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')


class FullTextIndex(db.Model):
    """نموذج فهرس البحث النصي"""
    __tablename__ = 'fulltext_indexes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(36), nullable=False)
    
    indexed_text = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.Text, nullable=True)  # Comma-separated
    
    last_indexed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== 12. MOBILE APPLICATION SUPPORT ====================

class MobileDevice(db.Model):
    """نموذج أجهزة الموبايل المسجلة"""
    __tablename__ = 'mobile_devices'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    device_id = db.Column(db.String(255), unique=True, nullable=False)  # Unique device identifier
    device_name = db.Column(db.String(255), nullable=False)  # Device model
    device_type = db.Column(db.String(50), nullable=False)  # ios, android, web
    
    os_version = db.Column(db.String(50), nullable=True)
    app_version = db.Column(db.String(50), nullable=True)
    
    fcm_token = db.Column(db.String(255), nullable=True)  # Firebase Cloud Messaging token
    push_enabled = db.Column(db.Boolean, default=True)
    
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<MobileDevice {self.device_name}>'


class MobileNotification(db.Model):
    """نموذج إشعارات الموبايل"""
    __tablename__ = 'mobile_notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(36), db.ForeignKey('mobile_devices.id'), nullable=False)
    
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    notification_type = db.Column(db.String(50), nullable=False)  # scan, alert, approval, inventory
    related_entity_type = db.Column(db.String(50), nullable=True)  # Asset, Item, etc
    related_entity_id = db.Column(db.String(36), nullable=True)
    
    data = db.Column(db.Text, nullable=True)  # JSON data
    
    is_read = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    
    sent_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    device = db.relationship('MobileDevice')
    
    def __repr__(self):
        return f'<MobileNotification {self.title}>'


class PushSubscription(db.Model):
    """نموذج تخزين اشتراكات Web Push (VAPID)"""
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.String(255), nullable=True)
    auth = db.Column(db.String(255), nullable=True)
    content_encoding = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh,
                'auth': self.auth
            }
        }


class OfflineData(db.Model):
    """نموذج البيانات المتزامنة (للعمل بدون إنترنت)"""
    __tablename__ = 'offline_data'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.String(36), db.ForeignKey('mobile_devices.id'), nullable=False)
    
    data_type = db.Column(db.String(50), nullable=False)  # asset, item, location
    entity_id = db.Column(db.String(36), nullable=False)
    
    data_snapshot = db.Column(db.Text, nullable=False)  # JSON data
    last_synced = db.Column(db.DateTime, default=datetime.utcnow)
    is_synced = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    device = db.relationship('MobileDevice')


class QRCodeMapping(db.Model):
    """نموذج لربط QR codes بالأصول"""
    __tablename__ = 'qr_code_mappings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    qr_value = db.Column(db.String(255), unique=True, nullable=False)  # Unique QR data
    entity_type = db.Column(db.String(50), nullable=False)  # asset, item, location
    entity_id = db.Column(db.String(36), nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    scans_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_scanned = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<QRCodeMapping {self.qr_value}>'


# ==================== 13. ADVANCED ANALYTICS DASHBOARD ====================

class DashboardMetric(db.Model):
    """نموذج مؤشرات لوحة التحكم التحليلية"""
    __tablename__ = 'dashboard_metrics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    metric_name = db.Column(db.String(255), nullable=False)  # اسم المؤشر
    metric_key = db.Column(db.String(100), unique=True, nullable=False)  # مفتاح فريد
    metric_type = db.Column(db.String(50), nullable=False)  # number, percentage, currency, trend
    
    category = db.Column(db.String(100), nullable=False)  # inventory, assets, suppliers, etc
    
    value = db.Column(db.Float, nullable=True)  # القيمة الحالية
    previous_value = db.Column(db.Float, nullable=True)  # القيمة السابقة
    trend = db.Column(db.String(20), nullable=True)  # up, down, stable
    
    description = db.Column(db.Text, nullable=True)
    
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    calculation_frequency = db.Column(db.String(50), default="daily")  # hourly, daily, weekly, monthly
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DashboardMetric {self.metric_name}>'


class AnalyticsReport(db.Model):
    """نموذج التقارير التحليلية"""
    __tablename__ = 'analytics_reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    report_name = db.Column(db.String(255), nullable=False)  # اسم التقرير
    report_type = db.Column(db.String(50), nullable=False)  # inventory_trend, asset_depreciation, spending_analysis, etc
    
    description = db.Column(db.Text, nullable=True)
    
    date_range_start = db.Column(db.DateTime, nullable=True)
    date_range_end = db.Column(db.DateTime, nullable=True)
    
    metrics_data = db.Column(db.Text, nullable=True)  # JSON data للرسوم البيانية
    summary_data = db.Column(db.Text, nullable=True)  # JSON ملخص البيانات
    
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    is_scheduled = db.Column(db.Boolean, default=False)
    schedule_frequency = db.Column(db.String(50), nullable=True)  # daily, weekly, monthly
    last_generated = db.Column(db.DateTime, nullable=True)
    
    is_public = db.Column(db.Boolean, default=False)  # هل يمكن مشاركته
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User')
    
    def __repr__(self):
        return f'<AnalyticsReport {self.report_name}>'


class KPITracker(db.Model):
    """نموذج متتبع المؤشرات الرئيسية (KPI)"""
    __tablename__ = 'kpi_trackers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    kpi_name = db.Column(db.String(255), nullable=False)  # اسم المؤشر الرئيسي
    kpi_description = db.Column(db.Text, nullable=True)
    
    target_value = db.Column(db.Float, nullable=False)  # القيمة المستهدفة
    current_value = db.Column(db.Float, nullable=True)  # القيمة الحالية
    
    measurement_unit = db.Column(db.String(50), nullable=True)  # %, ج.د, وحدة، إلخ
    
    performance_status = db.Column(db.String(20), default="on_track")  # on_track, at_risk, off_track
    completion_percentage = db.Column(db.Float, default=0)  # نسبة الإنجاز
    
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    
    review_frequency = db.Column(db.String(50), default="monthly")  # weekly, monthly, quarterly
    last_reviewed = db.Column(db.DateTime, nullable=True)
    
    owner = db.relationship('User')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<KPITracker {self.kpi_name}>'


# ==================== 14. SMART ALERT SYSTEM ====================

class SmartAlert(db.Model):
    """نموذج التنبيهات الذكية المحسّنة"""
    __tablename__ = 'smart_alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    alert_name = db.Column(db.String(255), nullable=False)  # اسم التنبيه
    alert_type = db.Column(db.String(50), nullable=False)  # low_stock, expiry_warning, maintenance_due, asset_status_change, budget_threshold, unusual_activity
    
    entity_type = db.Column(db.String(50), nullable=False)  # Item, AssetRegistration, Supplier, etc
    entity_id = db.Column(db.String(36), nullable=True)  # ID الكيان المراقب
    
    condition = db.Column(db.String(255), nullable=False)  # شرط التنبيه
    threshold_value = db.Column(db.Float, nullable=True)  # قيمة الحد الأدنى
    
    priority = db.Column(db.String(20), default="medium")  # critical, high, medium, low
    
    # قنوات الإخطار
    notify_via_email = db.Column(db.Boolean, default=True)
    notify_via_sms = db.Column(db.Boolean, default=False)
    notify_via_system = db.Column(db.Boolean, default=True)
    notify_via_push = db.Column(db.Boolean, default=True)
    
    # الأشخاص المسؤولون عن التنبيه
    assigned_to_ids = db.Column(db.Text, nullable=True)  # JSON list of user IDs
    
    is_active = db.Column(db.Boolean, default=True)
    
    # آخر تفعيل للتنبيه
    last_triggered = db.Column(db.DateTime, nullable=True)
    trigger_count = db.Column(db.Integer, default=0)
    
    # إعادة التنبيه
    renotify_interval = db.Column(db.Integer, nullable=True)  # بالساعات
    last_notified = db.Column(db.DateTime, nullable=True)
    
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User')
    
    def __repr__(self):
        return f'<SmartAlert {self.alert_name}>'
    
    def get_assigned_users(self):
        """الحصول على المستخدمين المعينين"""
        if self.assigned_to_ids:
            import json
            return json.loads(self.assigned_to_ids)
        return []


class AlertHistory(db.Model):
    """نموذج سجل التنبيهات"""
    __tablename__ = 'alert_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    alert_id = db.Column(db.String(36), db.ForeignKey('smart_alerts.id'), nullable=False)
    
    triggered_value = db.Column(db.Float, nullable=True)  # القيمة التي تسببت في التنبيه
    trigger_details = db.Column(db.Text, nullable=True)  # JSON تفاصيل التنبيه
    
    message = db.Column(db.Text, nullable=False)  # رسالة التنبيه
    
    status = db.Column(db.String(50), default="pending")  # pending, notified, acknowledged, resolved
    acknowledged_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    
    resolution_notes = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    alert = db.relationship('SmartAlert', backref='history')
    acknowledged_by = db.relationship('User', foreign_keys=[acknowledged_by_id])
    
    def __repr__(self):
        return f'<AlertHistory {self.id}>'


# ==================== 15. DOCUMENT MANAGEMENT ====================

class Document(db.Model):
    """نموذج إدارة الوثائق"""
    __tablename__ = 'documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    document_name = db.Column(db.String(255), nullable=False)  # اسم الوثيقة
    document_type = db.Column(db.String(50), nullable=False)  # contract, invoice, purchase_order, quote, report, other
    
    description = db.Column(db.Text, nullable=True)
    
    # ملف الوثيقة
    file_path = db.Column(db.String(255), nullable=False)  # مسار الملف
    file_size = db.Column(db.Integer, nullable=True)  # حجم الملف بالبايت
    file_type = db.Column(db.String(20), nullable=True)  # pdf, docx, xlsx, jpg, etc
    
    # الربط بالكيانات
    related_entity_type = db.Column(db.String(50), nullable=True)  # Supplier, PurchaseOrder, etc
    related_entity_id = db.Column(db.String(36), nullable=True)  # ID الكيان
    
    # معلومات الوثيقة
    document_number = db.Column(db.String(100), nullable=True)  # رقم الوثيقة/العقد
    document_date = db.Column(db.DateTime, nullable=True)  # تاريخ الوثيقة
    
    expiry_date = db.Column(db.DateTime, nullable=True)  # تاريخ انتهاء الصلاحية (للعقود)
    
    # التصنيفات والعلامات
    category = db.Column(db.String(100), nullable=True)  # فئة الوثيقة
    tags = db.Column(db.Text, nullable=True)  # JSON tags
    
    # الحالة والموافقة
    status = db.Column(db.String(50), default="draft")  # draft, approved, rejected, archived
    
    # التوقيع الإلكتروني
    requires_signature = db.Column(db.Boolean, default=False)
    is_signed = db.Column(db.Boolean, default=False)
    signed_by_ids = db.Column(db.Text, nullable=True)  # JSON list of user IDs who signed
    
    # الإصدارات
    version_number = db.Column(db.Integer, default=1)
    parent_document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=True)  # للتعامل مع الإصدارات
    
    # معلومات الإنشاء والتعديل
    uploaded_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    last_modified_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # الوصول والمشاركة
    is_public = db.Column(db.Boolean, default=False)
    shared_with_ids = db.Column(db.Text, nullable=True)  # JSON list of user IDs
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id])
    last_modified_by = db.relationship('User', foreign_keys=[last_modified_by_id])
    
    # العلاقات
    versions = db.relationship('Document', remote_side=[id], backref='parent')
    
    def __repr__(self):
        return f'<Document {self.document_name}>'
    
    def get_tags(self):
        """الحصول على العلامات"""
        if self.tags:
            import json
            return json.loads(self.tags)
        return []
    
    def get_shared_with(self):
        """الحصول على المستخدمين المشاركة معهم"""
        if self.shared_with_ids:
            import json
            return json.loads(self.shared_with_ids)
        return []


class DocumentVersion(db.Model):
    """نموذج إصدارات الوثائق"""
    __tablename__ = 'document_versions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    
    version_number = db.Column(db.Integer, nullable=False)
    
    file_path = db.Column(db.String(255), nullable=False)
    change_description = db.Column(db.Text, nullable=True)
    
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    document = db.relationship('Document', backref='all_versions')
    created_by = db.relationship('User')
    
    def __repr__(self):
        return f'<DocumentVersion {self.document_id} v{self.version_number}>'


class DocumentComment(db.Model):
    """نموذج التعليقات على الوثائق"""
    __tablename__ = 'document_comments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    
    comment_text = db.Column(db.Text, nullable=False)
    
    commented_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # التعليقات المرتبطة
    reply_to_id = db.Column(db.String(36), db.ForeignKey('document_comments.id'), nullable=True)
    
    # الإشارات المرئية
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    document = db.relationship('Document', backref='comments')
    commented_by = db.relationship('User', foreign_keys=[commented_by_id])
    replies = db.relationship('DocumentComment', remote_side=[id], backref='parent_comment')


# ============== ADVANCED FEATURES - PHASE 3 ==============

# 1. EMAIL NOTIFICATIONS SYSTEM
class EmailNotification(db.Model):
    """نموذج الإشعارات عبر البريد الإلكتروني"""
    __tablename__ = 'email_notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    recipient_email = db.Column(db.String(120), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    
    notification_type = db.Column(db.String(50), nullable=False)  # alert, report, system, custom
    priority = db.Column(db.String(20), default='normal')  # high, normal, low
    
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    
    attachment_path = db.Column(db.String(255), nullable=True)
    
    retry_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='email_notifications')
    
    def __repr__(self):
        return f'<EmailNotification {self.recipient_email}>'


class EmailTemplate(db.Model):
    """نموذج قوالب البريد الإلكتروني"""
    __tablename__ = 'email_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    template_name = db.Column(db.String(100), unique=True, nullable=False)
    template_key = db.Column(db.String(100), unique=True, nullable=False)
    
    subject_template = db.Column(db.String(255), nullable=False)
    body_template = db.Column(db.Text, nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.template_name}>'


# 2. QR CODE & BARCODE SYSTEM
class QRBarcode(db.Model):
    """نموذج أكواد QR والباركود"""
    __tablename__ = 'qr_barcodes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    code_type = db.Column(db.String(20), nullable=False)  # qr_code, barcode
    code_value = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    entity_type = db.Column(db.String(50), nullable=False)  # asset, item, supplier
    entity_id = db.Column(db.String(36), nullable=False, index=True)
    
    image_path = db.Column(db.String(255), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scanned_count = db.Column(db.Integer, default=0)
    last_scanned_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<QRBarcode {self.code_type}:{self.code_value}>'


class QRBarcodeLog(db.Model):
    """نموذج سجل مسح أكواد QR والباركود"""
    __tablename__ = 'qr_barcode_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    qr_barcode_id = db.Column(db.String(36), db.ForeignKey('qr_barcodes.id'), nullable=False)
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    action = db.Column(db.String(50), nullable=False)  # scan, generate, update
    device_info = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    qr_barcode = db.relationship('QRBarcode', backref='scan_logs')
    user = db.relationship('User', backref='qr_scans')
    
    def __repr__(self):
        return f'<QRBarcodeLog {self.qr_barcode_id}>'


# 3. PDF EXPORT SYSTEM
class PDFExportJob(db.Model):
    """نموذج مهام تصدير PDF"""
    __tablename__ = 'pdf_export_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    job_name = db.Column(db.String(255), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)  # report, inventory, assets, suppliers
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    source_data = db.Column(db.JSON, nullable=True)  # Filters and parameters
    
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    
    file_path = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.BigInteger, nullable=True)
    
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    expires_at = db.Column(db.DateTime, nullable=True)  # Auto-delete after 7 days
    
    user = db.relationship('User', backref='pdf_exports')
    
    def __repr__(self):
        return f'<PDFExportJob {self.job_name}>'


# 4. REAL-TIME UPDATES
class RealTimeEvent(db.Model):
    """نموذج الأحداث في الوقت الفعلي"""
    __tablename__ = 'realtime_events'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    event_type = db.Column(db.String(100), nullable=False)  # item_added, stock_changed, etc
    entity_type = db.Column(db.String(50), nullable=False)  # item, asset, supplier
    entity_id = db.Column(db.String(36), nullable=False)
    
    event_data = db.Column(db.JSON, nullable=True)
    
    triggered_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    is_broadcasted = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    triggered_by = db.relationship('User', backref='triggered_events')
    
    def __repr__(self):
        return f'<RealTimeEvent {self.event_type}>'


# 5. EXTERNAL INTEGRATION
class ExternalIntegration(db.Model):
    """نموذج التكاملات الخارجية"""
    __tablename__ = 'external_integrations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    integration_name = db.Column(db.String(100), nullable=False, unique=True)
    integration_type = db.Column(db.String(50), nullable=False)  # accounting, erp, crm, api
    
    api_endpoint = db.Column(db.String(500), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    api_secret = db.Column(db.String(255), nullable=True)
    
    webhook_url = db.Column(db.String(500), nullable=True)
    webhook_key = db.Column(db.String(255), nullable=True)
    
    is_active = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    
    last_sync = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.Text, nullable=True)
    
    config_data = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    created_by = db.relationship('User', backref='integrations')
    
    def __repr__(self):
        return f'<ExternalIntegration {self.integration_name}>'


class IntegrationLog(db.Model):
    """نموذج سجل التكاملات الخارجية"""
    __tablename__ = 'integration_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    integration_id = db.Column(db.String(36), db.ForeignKey('external_integrations.id'), nullable=False)
    
    action = db.Column(db.String(100), nullable=False)  # sync, push, pull, test
    status = db.Column(db.String(50), nullable=False)  # success, failed, pending
    
    request_data = db.Column(db.JSON, nullable=True)
    response_data = db.Column(db.JSON, nullable=True)
    
    error_message = db.Column(db.Text, nullable=True)
    
    execution_time_ms = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    integration = db.relationship('ExternalIntegration', backref='logs')
    
    def __repr__(self):
        return f'<IntegrationLog {self.integration_id}>'


# 6. ADVANCED AUDIT LOGS
class AdvancedAuditLog(db.Model):
    """نموذج سجلات التدقيق المتقدمة"""
    __tablename__ = 'advanced_audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    action = db.Column(db.String(255), nullable=False)  # create, update, delete, view, export
    entity_type = db.Column(db.String(50), nullable=False)  # item, asset, user, supplier
    entity_id = db.Column(db.String(36), nullable=False)
    
    old_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)
    
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    status = db.Column(db.String(50), default='success')  # success, failed
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AdvancedAuditLog {self.action}:{self.entity_type}>'


class MobileAPIKey(db.Model):
    """نموذج مفاتيح API للتطبيقات المحمولة"""
    __tablename__ = 'mobile_api_keys'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    api_key = db.Column(db.String(255), unique=True, nullable=False)
    api_secret = db.Column(db.String(255), nullable=False)
    
    device_id = db.Column(db.String(255), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    
    last_used = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref='mobile_api_keys')
    
    def __repr__(self):
        return f'<MobileAPIKey {self.user_id}>'


# 8. FEATURE FLAGS & CONFIGURATION
class FeatureFlag(db.Model):
    """نموذج علامات الميزات"""
    __tablename__ = 'feature_flags'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    flag_name = db.Column(db.String(100), unique=True, nullable=False)
    flag_description = db.Column(db.Text, nullable=True)
    
    is_enabled = db.Column(db.Boolean, default=False)
    
    feature_type = db.Column(db.String(50), nullable=False)  # email, qr, pdf, realtime, integration, audit, mobile
    
    config_data = db.Column(db.JSON, nullable=True)
    
    enabled_for_roles = db.Column(db.JSON, nullable=True)  # List of roles
    enabled_for_users = db.Column(db.JSON, nullable=True)  # List of user IDs
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    updated_by = db.relationship('User', backref='feature_flag_updates')
    
    def __repr__(self):
        return f'<FeatureFlag {self.flag_name}>'


# ==================== 16. EMPLOYEE STOCK REQUESTS ====================

class StockRequest(db.Model):
    """نموذج طلبات الموظفين للمنتجات"""
    __tablename__ = 'stock_requests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # معلومات الطلب الأساسية
    request_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # الموظف الطالب
    requested_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # حالة الطلب: pending, approved, rejected, delivered
    status = db.Column(db.String(50), default='pending')
    
    # معلومات الموافقة
    approved_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)  # من وافق
    approval_date = db.Column(db.DateTime, nullable=True)
    
    # معلومات الرفض
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # معلومات التسليم
    delivered_date = db.Column(db.DateTime, nullable=True)
    
    # توقيع الموظف وقت الاستلام (التاريخ والوقت)
    employee_signature_date = db.Column(db.DateTime, nullable=True)
    
    # توقيع المسؤول (التاريخ والوقت)
    approver_signature_date = db.Column(db.DateTime, nullable=True)
    
    # ملاحظات
    notes = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)  # ملاحظات داخلية للمسؤول
    
    # الأرقام التسلسلية
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='stock_requests')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_requests')
    items = db.relationship('StockRequestItem', backref='request', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StockRequest {self.request_number}>'
    
    @property
    def total_items(self):
        """عدد أنواع المنتجات المطلوبة"""
        return len(self.items)
    
    @property
    def total_quantity(self):
        """الكمية الإجمالية المطلوبة"""
        return sum(item.quantity for item in self.items)
    
    @property
    def total_cost(self):
        """التكلفة الإجمالية للطلب"""
        return sum(item.total_price for item in self.items)
    
    def get_status_display(self):
        """الحصول على نص حالة الطلب"""
        status_map = {
            'pending': 'قيد الانتظار',
            'approved': 'موافق عليه',
            'rejected': 'مرفوض',
            'delivered': 'تم التسليم'
        }
        return status_map.get(self.status, self.status)


class StockRequestItem(db.Model):
    """نموذج تفاصيل طلب المنتجات"""
    __tablename__ = 'stock_request_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # الربط بالطلب الرئيسي
    request_id = db.Column(db.String(36), db.ForeignKey('stock_requests.id'), nullable=False)
    
    # المنتج المطلوب
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    # الكمية والسعر
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=True)  # السعر في وقت الطلب
    
    # حالة المنتج في الطلب
    item_status = db.Column(db.String(50), default='pending')  # pending, delivered, partial
    delivered_quantity = db.Column(db.Float, default=0)  # الكمية المسلمة فعلاً
    
    # ملاحظات على المنتج
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    item = db.relationship('Item', backref='requested_items')
    
    def __repr__(self):
        return f'<StockRequestItem {self.id}>'
    
    @property
    def total_price(self):
        """السعر الإجمالي للصنف"""
        if self.unit_price:
            return self.quantity * self.unit_price
        return 0


# ==================== جديد: نماذج الميزات العشر الإضافية ====================

# 1. تحليل ABC للمخزون
class InventoryABCAnalysis(db.Model):
    """نموذج تحليل ABC للمخزون"""
    __tablename__ = 'inventory_abc_analysis'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    analysis_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    period = db.Column(db.String(50), nullable=False)  # monthly, quarterly, yearly
    
    # قيم التحليل
    abc_category = db.Column(db.String(1), nullable=False)  # A, B, C
    annual_consumption = db.Column(db.Float, nullable=False)  # الاستهلاك السنوي
    annual_value = db.Column(db.Float, nullable=False)  # القيمة السنوية
    consumption_rate = db.Column(db.Float, nullable=False)  # معدل الاستهلاك
    
    percentage_of_total = db.Column(db.Float, nullable=False)  # النسبة المئوية
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<InventoryABCAnalysis {self.item_id}:{self.abc_category}>'


# 2. عمليات الجرد الدورية
class InventoryCount(db.Model):
    """نموذج عمليات الجرد الدورية"""
    __tablename__ = 'inventory_counts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    count_number = db.Column(db.String(50), unique=True, nullable=False)
    
    count_type = db.Column(db.String(50), nullable=False)  # full, partial, cycle
    count_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), default='in_progress')  # in_progress, completed, verified
    
    warehouse_location = db.Column(db.String(255), nullable=True)
    started_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    completed_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # العلاقات
    started_by = db.relationship('User', foreign_keys=[started_by_id])
    completed_by = db.relationship('User', foreign_keys=[completed_by_id])
    count_items = db.relationship('InventoryCountItem', backref='count', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<InventoryCount {self.count_number}>'


class InventoryCountItem(db.Model):
    """نموذج تفاصيل عمليات الجرد"""
    __tablename__ = 'inventory_count_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    count_id = db.Column(db.String(36), db.ForeignKey('inventory_counts.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    system_quantity = db.Column(db.Float, nullable=False)  # الكمية في النظام
    physical_count = db.Column(db.Float, nullable=True)  # الكمية الفعلية
    variance = db.Column(db.Float, nullable=True)  # الفرق
    variance_percentage = db.Column(db.Float, nullable=True)
    
    variance_reason = db.Column(db.String(255), nullable=True)  # السبب (loss, damage, etc)
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<InventoryCountItem {self.count_id}:{self.item_id}>'


# 3. إدارة المستودعات
class Warehouse(db.Model):
    """نموذج المستودعات"""
    __tablename__ = 'warehouses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    
    location = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    
    manager_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    capacity = db.Column(db.Float, nullable=True)  # السعة الإجمالية
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    manager = db.relationship('User')
    warehouse_items = db.relationship('WarehouseInventory', backref='warehouse', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Warehouse {self.name}>'


class WarehouseInventory(db.Model):
    """نموذج المخزون في المستودع"""
    __tablename__ = 'warehouse_inventory'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = db.Column(db.String(36), db.ForeignKey('warehouses.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    quantity_on_hand = db.Column(db.Float, default=0)
    reserved_quantity = db.Column(db.Float, default=0)
    available_quantity = db.Column(db.Float, default=0)
    
    location_code = db.Column(db.String(50), nullable=True)  # الرف/المنطقة
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = db.relationship('Item')
    
    __table_args__ = (db.UniqueConstraint('warehouse_id', 'item_id', name='unique_warehouse_item'),)
    
    def __repr__(self):
        return f'<WarehouseInventory {self.warehouse_id}:{self.item_id}>'


# 4. تكاليف المخزون
class InventoryCostAnalysis(db.Model):
    """نموذج تحليل تكاليف المخزون"""
    __tablename__ = 'inventory_cost_analysis'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    analysis_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    period = db.Column(db.String(50), nullable=False)  # monthly, quarterly, yearly
    
    # تكاليف الاحتفاظ بالمخزون
    holding_cost = db.Column(db.Float, default=0)  # تكلفة الاحتفاظ
    holding_cost_percentage = db.Column(db.Float, default=20)  # نسبة التكلفة
    
    ordering_cost = db.Column(db.Float, default=0)  # تكلفة الطلب
    shortage_cost = db.Column(db.Float, default=0)  # تكلفة النقص
    
    total_inventory_value = db.Column(db.Float, default=0)  # القيمة الإجمالية
    average_inventory = db.Column(db.Float, default=0)  # متوسط المخزون
    
    profitability = db.Column(db.Float, nullable=True)  # الربحية
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<InventoryCostAnalysis {self.item_id}>'


# 5. توصيات الطلب
class RecommendedOrder(db.Model):
    """نموذج توصيات الطلب المثالي"""
    __tablename__ = 'recommended_orders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    recommendation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # المؤشرات
    eoq = db.Column(db.Float, nullable=False)  # كمية الطلب الاقتصادية
    reorder_point = db.Column(db.Float, nullable=False)  # نقطة إعادة الطلب
    reorder_level = db.Column(db.Float, nullable=False)  # مستوى إعادة الطلب
    
    recommended_quantity = db.Column(db.Float, nullable=False)
    recommended_supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=True)
    
    urgency = db.Column(db.String(50), default='normal')  # normal, urgent, critical
    reason = db.Column(db.String(255), nullable=False)
    
    status = db.Column(db.String(50), default='pending')  # pending, approved, ordered, rejected
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    item = db.relationship('Item')
    supplier = db.relationship('Supplier')
    
    def __repr__(self):
        return f'<RecommendedOrder {self.item_id}>'


# 6. التنبؤات
class InventoryForecast(db.Model):
    """نموذج التنبؤات بالمخزون"""
    __tablename__ = 'inventory_forecasts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    forecast_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    forecast_period = db.Column(db.String(50), nullable=False)  # next_week, next_month, next_quarter
    
    forecasted_demand = db.Column(db.Float, nullable=False)
    confidence_level = db.Column(db.Float, nullable=False)  # 0-100%
    
    # النموذج المستخدم
    forecast_method = db.Column(db.String(100), nullable=False)  # moving_average, exponential_smoothing, linear_regression
    
    # القيم المتوقعة
    expected_stock_level = db.Column(db.Float, nullable=False)
    will_stock_out = db.Column(db.Boolean, default=False)
    estimated_stockout_date = db.Column(db.Date, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<InventoryForecast {self.item_id}>'


# 7. سجل الأسعار
class PriceHistory(db.Model):
    """نموذج سجل الأسعار التاريخي"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=True)
    
    price_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    unit_price = db.Column(db.Float, nullable=False)
    
    quantity_purchased = db.Column(db.Float, nullable=True)
    
    price_source = db.Column(db.String(50), nullable=False)  # purchase_order, invoice, market
    
    # تتبع التغييرات
    price_change = db.Column(db.Float, nullable=True)  # التغير عن السعر السابق
    price_change_percentage = db.Column(db.Float, nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    item = db.relationship('Item')
    supplier = db.relationship('Supplier')
    
    def __repr__(self):
        return f'<PriceHistory {self.item_id}:{self.price_date}>'


# 8. أداء الموردين
class SupplierPerformance(db.Model):
    """نموذج تقييم أداء الموردين"""
    __tablename__ = 'supplier_performance'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=False)
    
    evaluation_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    period = db.Column(db.String(50), nullable=False)  # monthly, quarterly, yearly
    
    # المؤشرات
    quality_score = db.Column(db.Float, default=0)  # درجة الجودة (0-100)
    delivery_score = db.Column(db.Float, default=0)  # درجة التسليم (0-100)
    price_competitiveness = db.Column(db.Float, default=0)  # تنافسية السعر (0-100)
    communication_score = db.Column(db.Float, default=0)  # درجة التواصل (0-100)
    
    # المؤشرات المشتقة
    on_time_delivery_percentage = db.Column(db.Float, default=0)
    defect_rate = db.Column(db.Float, default=0)
    average_lead_time_days = db.Column(db.Float, default=0)
    
    # الدرجة الإجمالية
    overall_score = db.Column(db.Float, default=0)
    performance_rating = db.Column(db.String(20), default='good')  # excellent, good, average, poor
    
    recommendations = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    supplier = db.relationship('Supplier')
    
    def __repr__(self):
        return f'<SupplierPerformance {self.supplier_id}>'


# 9. سجل مسح QR/Barcode المتقدم
class QRBarcodeConfig(db.Model):
    """نموذج إعدادات QR و Barcode"""
    __tablename__ = 'qrbarcode_config'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False, unique=True)
    
    barcode_type = db.Column(db.String(20), default='CODE128')  # CODE128, EAN13, QR
    barcode_value = db.Column(db.String(255), nullable=False, unique=True)
    
    qr_enabled = db.Column(db.Boolean, default=True)
    barcode_enabled = db.Column(db.Boolean, default=True)
    
    last_scanned = db.Column(db.DateTime, nullable=True)
    scan_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<QRBarcodeConfig {self.item_id}>'


class QRBarcodeScan(db.Model):
    """نموذج سجل عمليات المسح المتقدمة"""
    __tablename__ = 'qrbarcode_scans'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = db.Column(db.String(36), db.ForeignKey('qrbarcode_config.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    scan_type = db.Column(db.String(20), nullable=False)  # 'qr', 'barcode'
    action = db.Column(db.String(50), nullable=False)  # 'check_in', 'check_out', 'inventory', 'maintenance', 'transfer'
    
    device_info = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    gps_coordinates = db.Column(db.String(100), nullable=True)
    
    quantity_scanned = db.Column(db.Float, default=1)
    
    notes = db.Column(db.Text, nullable=True)
    
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    config = db.relationship('QRBarcodeConfig')
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<QRBarcodeScan {self.id}>'


# 10. عمليات الإنذارات الذكية المتقدمة
class Notification(db.Model):
    """نموذج الإشعارات"""
    __tablename__ = 'notifications'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    title = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, warning, success, error
    
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # رابط العملية المرتبطة
    related_url = db.Column(db.String(255), nullable=True)
    related_id = db.Column(db.String(36), nullable=True)
    related_type = db.Column(db.String(50), nullable=True)  # item, transaction, order, request, etc
    
    # قنوات الإشعار
    channels = db.Column(db.String(255), default='dashboard')  # dashboard, email, sms, push
    sent_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications', overlaps='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}:{self.title}>'
    
    def mark_as_read(self):
        """تحديد الإشعار كمقروء"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()


class SmartInventoryAlert(db.Model):
    """نموذج إنذارات المخزون الذكية"""
    __tablename__ = 'smart_inventory_alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
    
    alert_type = db.Column(db.String(50), nullable=False)  # low_stock, slow_moving, overstock, price_alert, quality_alert
    
    threshold_value = db.Column(db.Float, nullable=False)  # قيمة الحد
    current_value = db.Column(db.Float, nullable=False)  # القيمة الحالية
    
    severity = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    
    triggered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # الإجراء المقترح
    recommended_action = db.Column(db.String(255), nullable=True)
    action_taken = db.Column(db.String(255), nullable=True)
    
    # إشعارات
    notification_channels = db.Column(db.String(255), default='dashboard,email')  # dashboard, email, sms, push
    notified_at = db.Column(db.DateTime, nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    
    is_resolved = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<SmartInventoryAlert {self.item_id}:{self.alert_type}>'


# ==================== RESTAURANT ADVANCED FEATURES ====================

# 1. WASTE MANAGEMENT - إدارة الفاقد والهدر
class FoodWaste(db.Model):
    """نموذج تسجيل الفاقد والهدر الغذائي"""
    __tablename__ = 'food_waste'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # معلومات الوجبة/المكون
    meal_record_id = db.Column(db.String(36), db.ForeignKey('meal_records.id'), nullable=True)
    item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=True)
    recipe_id = db.Column(db.String(36), db.ForeignKey('recipes.id'), nullable=True)
    
    # تفاصيل الهدر
    waste_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    waste_reason = db.Column(db.String(100), nullable=False)  # spoilage, overproduction, quality_issue, expired, accident, other
    
    quantity_wasted = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    
    # التقدير المالي
    estimated_unit_cost = db.Column(db.Float, nullable=False, default=0)
    total_waste_value = db.Column(db.Float, nullable=False, default=0)  # quantity * unit_cost
    
    # المسؤول والوثائق
    reported_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    description = db.Column(db.Text, nullable=True)
    photo_path = db.Column(db.String(255), nullable=True)  # صورة الهدر
    
    is_approved = db.Column(db.Boolean, default=False)
    approval_date = db.Column(db.DateTime, nullable=True)
    approval_notes = db.Column(db.Text, nullable=True)
    
    # يمكن اتخاذ إجراء
    action_taken = db.Column(db.String(255), nullable=True)  # الإجراء المتخذ لتجنب تكراره
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    meal_record = db.relationship('MealRecord', foreign_keys=[meal_record_id])
    item = db.relationship('Item', foreign_keys=[item_id])
    recipe = db.relationship('Recipe', foreign_keys=[recipe_id])
    reported_by = db.relationship('User', foreign_keys=[reported_by_id], backref='waste_reports')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    
    def __repr__(self):
        return f'<FoodWaste {self.waste_date}:{self.quantity_wasted}>'
    
    def calculate_waste_value(self):
        """حساب القيمة الإجمالية للهدر"""
        self.total_waste_value = self.quantity_wasted * self.estimated_unit_cost
        return self.total_waste_value


class WasteAnalysis(db.Model):
    """نموذج تحليل الهدر والإحصائيات"""
    __tablename__ = 'waste_analysis'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    analysis_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    period = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly
    
    # إحصائيات الهدر
    total_waste_quantity = db.Column(db.Float, default=0)
    total_waste_value = db.Column(db.Float, default=0)
    waste_count = db.Column(db.Integer, default=0)
    
    # نسبة الهدر
    waste_percentage = db.Column(db.Float, default=0)  # نسبة من إجمالي الإنتاج
    
    # تصنيف أسباب الهدر
    spoilage_count = db.Column(db.Integer, default=0)
    overproduction_count = db.Column(db.Integer, default=0)
    quality_issue_count = db.Column(db.Integer, default=0)
    expired_count = db.Column(db.Integer, default=0)
    accident_count = db.Column(db.Integer, default=0)
    other_count = db.Column(db.Integer, default=0)
    
    # الأصناف الأكثر هدراً
    top_wasted_items = db.Column(db.Text, nullable=True)  # JSON format
    
    # الملاحظات والتوصيات
    notes = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)  # توصيات تحسينية
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WasteAnalysis {self.analysis_date}>'


# 2. DEMAND FORECASTING - توقعات الطلب والاستهلاك
class DemandForecast(db.Model):
    """نموذج توقعات الطلب على الوجبات"""
    __tablename__ = 'demand_forecasts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    forecast_date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)  # breakfast, lunch, dinner
    
    # البيانات المتوقعة
    forecasted_portions = db.Column(db.Integer, nullable=False)  # عدد الحصص المتوقعة
    confidence_level = db.Column(db.Float, nullable=False, default=0.8)  # مستوى الثقة (0-1)
    
    # الفعلي بعد الوجبة
    actual_portions = db.Column(db.Integer, nullable=True)
    actual_consumption = db.Column(db.Float, nullable=True)  # معدل الاستهلاك الفعلي
    
    # الانحراف
    forecast_error = db.Column(db.Float, nullable=True)  # الفرق بين التوقع والفعلي
    error_percentage = db.Column(db.Float, nullable=True)  # نسبة الخطأ
    
    # طريقة التوقع
    forecasting_method = db.Column(db.String(50), default='statistical')  # statistical, ml_based, manual, historical_average
    
    # عوامل التأثير
    special_event = db.Column(db.Boolean, default=False)  # هل هناك حدث خاص
    event_description = db.Column(db.String(255), nullable=True)
    
    day_of_week = db.Column(db.String(20), nullable=True)  # monday, tuesday, etc
    is_holiday = db.Column(db.Boolean, default=False)
    
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DemandForecast {self.forecast_date}:{self.meal_type}>'
    
    def calculate_error(self):
        """حساب خطأ التوقع بعد حدوث الوجبة"""
        if self.actual_portions is not None:
            self.forecast_error = abs(self.forecasted_portions - self.actual_portions)
            self.error_percentage = (self.forecast_error / self.forecasted_portions * 100) if self.forecasted_portions > 0 else 0
            return self.error_percentage
        return None


class DemandAnalysis(db.Model):
    """نموذج تحليل الطلب والاستهلاك"""
    __tablename__ = 'demand_analysis'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    analysis_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    period = db.Column(db.String(50), nullable=False)  # daily, weekly, monthly
    
    # معدلات الاستهلاك
    average_portions_consumed = db.Column(db.Float, default=0)
    max_portions_consumed = db.Column(db.Float, default=0)
    min_portions_consumed = db.Column(db.Float, default=0)
    
    # معدلات التوقع
    forecast_accuracy = db.Column(db.Float, default=0)  # دقة التنبؤات
    average_error_percentage = db.Column(db.Float, default=0)
    
    # الأيام المزدحمة
    peak_days = db.Column(db.Text, nullable=True)  # JSON: {day: average_portions}
    
    # الوجبات الأكثر طلباً
    popular_meals = db.Column(db.Text, nullable=True)  # JSON format
    
    # التوصيات
    recommendations = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DemandAnalysis {self.analysis_date}>'


# 3. EMPLOYEE MEAL SUBSIDY/DISCOUNT - نظام دعم ووجبات الموظفين
class EmployeeMealSubsidy(db.Model):
    """نموذج دعم ووجبات الموظفين"""
    __tablename__ = 'employee_meal_subsidy'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # نوع الدعم
    subsidy_type = db.Column(db.String(50), nullable=False)  # percentage_discount, fixed_amount, free_meals, special_diet
    
    # قيمة الدعم
    subsidy_value = db.Column(db.Float, nullable=False)  # نسبة الخصم أو المبلغ الثابت
    subsidy_currency = db.Column(db.String(10), default='DZD')  # العملة
    
    # الفترة الزمنية
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    
    # الصلاحية
    is_active = db.Column(db.Boolean, default=True)
    
    # المبرر والموافقة
    reason = db.Column(db.String(255), nullable=False)  # سبب الدعم
    approved_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    approval_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    user = db.relationship('User', foreign_keys=[user_id], backref='meal_subsidies')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    
    def __repr__(self):
        return f'<EmployeeMealSubsidy {self.user_id}>'
    
    @property
    def is_valid(self):
        """التحقق من صلاحية الدعم"""
        today = datetime.utcnow().date()
        if not self.is_active:
            return False
        if self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True


class EmployeeMealTransaction(db.Model):
    """نموذج عمليات استهلاك الموظفين للوجبات"""
    __tablename__ = 'employee_meal_transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    meal_record_id = db.Column(db.String(36), db.ForeignKey('meal_records.id'), nullable=False)
    
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # التكلفة والدفع
    meal_cost = db.Column(db.Float, nullable=False)  # التكلفة الأصلية
    discount_percentage = db.Column(db.Float, default=0)  # نسبة الخصم المطبقة
    discount_amount = db.Column(db.Float, default=0)  # قيمة الخصم
    
    final_cost = db.Column(db.Float, nullable=False)  # السعر النهائي المدفوع
    
    # طريقة الدفع
    payment_method = db.Column(db.String(50), nullable=False)  # cash, subsidy, free, deferred
    
    # التسوية المالية
    is_settled = db.Column(db.Boolean, default=False)  # تم التسديد
    settlement_date = db.Column(db.DateTime, nullable=True)
    settlement_notes = db.Column(db.Text, nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    user = db.relationship('User', backref='meal_transactions')
    meal_record = db.relationship('MealRecord', backref='employee_transactions')
    
    def __repr__(self):
        return f'<EmployeeMealTransaction {self.user_id}:{self.transaction_date}>'
    
    def calculate_final_cost(self):
        """حساب التكلفة النهائية بعد تطبيق الخصم"""
        self.discount_amount = self.meal_cost * (self.discount_percentage / 100)
        self.final_cost = self.meal_cost - self.discount_amount
        return self.final_cost


class MealPayrollIntegration(db.Model):
    """نموذج ربط الوجبات برواتب الموظفين"""
    __tablename__ = 'meal_payroll_integration'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # فترة الراتب
    payroll_period = db.Column(db.String(50), nullable=False)  # YYYY-MM (e.g., 2024-01)
    
    # إجمالي تكاليف الوجبات
    total_meal_cost = db.Column(db.Float, default=0)
    total_subsidy_amount = db.Column(db.Float, default=0)
    total_employee_payment = db.Column(db.Float, default=0)
    
    # عدد الوجبات
    total_meals_consumed = db.Column(db.Integer, default=0)
    free_meals_count = db.Column(db.Integer, default=0)
    subsidized_meals_count = db.Column(db.Integer, default=0)
    
    # الحالة
    is_processed = db.Column(db.Boolean, default=False)
    processing_date = db.Column(db.DateTime, nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    user = db.relationship('User', backref='payroll_meal_records')
    
    def __repr__(self):
        return f'<MealPayrollIntegration {self.user_id}:{self.payroll_period}>'
    
    def calculate_totals(self):
        """حساب الإجماليات من العمليات"""
        transactions = EmployeeMealTransaction.query.filter(
            EmployeeMealTransaction.user_id == self.user_id,
            EmployeeMealTransaction.transaction_date.between(
                datetime.strptime(f"{self.payroll_period}-01", "%Y-%m-%d").date(),
                datetime.strptime(f"{self.payroll_period}-28", "%Y-%m-%d").date()
            )
        ).all()
        
        self.total_meal_cost = sum(t.meal_cost for t in transactions)
        self.total_subsidy_amount = sum(t.discount_amount for t in transactions)
        self.total_employee_payment = sum(t.final_cost for t in transactions)
        self.total_meals_consumed = len(transactions)
        
        return {
            'total_meal_cost': self.total_meal_cost,
            'total_subsidy': self.total_subsidy_amount,
            'employee_payment': self.total_employee_payment
        }


class EmployeeMealAlert(db.Model):
    """نموذج التنبيهات عند تجاوز حد المستحقات"""
    __tablename__ = 'employee_meal_alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # التنبيه
    alert_type = db.Column(db.String(50), nullable=False)  # threshold_exceeded, payment_due, etc
    alert_threshold = db.Column(db.Float, nullable=False)  # الحد المسموح
    current_amount = db.Column(db.Float, nullable=False)  # المبلغ الحالي
    alert_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # حالة التنبيه
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_date = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.String(255), nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    user = db.relationship('User', backref='meal_alerts')
    
    def __repr__(self):
        return f'<EmployeeMealAlert {self.user_id}:{self.alert_type}>'