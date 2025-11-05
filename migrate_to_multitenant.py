#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
سكريبت الترحيل إلى نظام Multi-Tenant
Migration Script to Multi-Tenant System

هذا السكريبت يقوم بـ:
1. إنشاء جداول VocationalCenter والجداول الجديدة
2. إضافة الأعمدة الجديدة (center_id) للجداول الموجودة
3. تهيئة بيانات المؤسسات
"""

from app import create_app, db
from models import (
    VocationalCenter, User, UserRole, UserPermission,
    Item, Supplier, Recipe, Transaction, MealRecord,
    PurchaseOrder, AssetRegistration, ActivityLog
)
from datetime import datetime
import sys

def migrate_to_multitenant():
    """تنفيذ الترحيل إلى نظام Multi-Tenant"""
    
    app = create_app('development')
    
    with app.app_context():
        try:
            print("=" * 80)
            print("🔄 بدء ترحيل النظام إلى Multi-Tenant")
            print("=" * 80)
            
            # 1. إنشاء جميع الجداول
            print("\n📊 إنشاء الجداول الجديدة...")
            db.create_all()
            print("✅ تم إنشاء الجداول بنجاح")
            
            # 2. إنشاء مركز تكوين افتراضي
            print("\n🏢 إنشاء المركز الافتراضي...")
            
            default_center = VocationalCenter.query.filter_by(code='DEFAULT').first()
            if not default_center:
                default_center = VocationalCenter(
                    name='المركز الافتراضي',
                    name_en='Default Center',
                    code='DEFAULT',
                    address='العنوان الافتراضي',
                    phone='+213555555555',
                    email='default@institution.dz',
                    director_name='مدير المركز',
                    status='active',
                    is_active=True
                )
                db.session.add(default_center)
                db.session.commit()
                print(f"✅ تم إنشاء المركز الافتراضي: {default_center.name}")
            else:
                print("✅ المركز الافتراضي موجود بالفعل")
            
            # 3. تحديث المستخدمين الموجودين (إذا لم يكن لديهم center_id)
            print("\n👥 تحديث المستخدمين الموجودين...")
            users_updated = 0
            
            for user in User.query.all():
                if user.center_id is None and user.role not in [UserRole.FOUNDER, UserRole.ADMIN]:
                    user.center_id = default_center.id
                    users_updated += 1
            
            if users_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {users_updated} مستخدم")
            else:
                print("ℹ️ لا يوجد مستخدمين يحتاجون تحديث")
            
            # 4. تحديث الأصناف الموجودة
            print("\n📦 تحديث الأصناف الموجودة...")
            items_updated = 0
            
            for item in Item.query.all():
                if item.center_id is None:
                    item.center_id = default_center.id
                    items_updated += 1
            
            if items_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {items_updated} أصنف")
            else:
                print("ℹ️ جميع الأصناف محدثة بالفعل")
            
            # 5. تحديث الموردين الموجودين
            print("\n🚚 تحديث الموردين الموجودين...")
            suppliers_updated = 0
            
            for supplier in Supplier.query.all():
                if supplier.center_id is None:
                    supplier.center_id = default_center.id
                    suppliers_updated += 1
            
            if suppliers_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {suppliers_updated} مورد")
            else:
                print("ℹ️ جميع الموردين محدثين بالفعل")
            
            # 6. تحديث الوصفات الموجودة
            print("\n👨‍🍳 تحديث الوصفات الموجودة...")
            recipes_updated = 0
            
            for recipe in Recipe.query.all():
                if recipe.center_id is None:
                    recipe.center_id = default_center.id
                    recipes_updated += 1
            
            if recipes_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {recipes_updated} وصفة")
            else:
                print("ℹ️ جميع الوصفات محدثة بالفعل")
            
            # 7. تحديث العمليات الموجودة
            print("\n📋 تحديث العمليات الموجودة...")
            transactions_updated = 0
            
            for transaction in Transaction.query.all():
                if transaction.center_id is None:
                    transaction.center_id = default_center.id
                    transactions_updated += 1
            
            if transactions_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {transactions_updated} عملية")
            else:
                print("ℹ️ جميع العمليات محدثة بالفعل")
            
            # 8. تحديث سجلات الوجبات
            print("\n🍽️ تحديث سجلات الوجبات...")
            meals_updated = 0
            
            for meal in MealRecord.query.all():
                if meal.center_id is None:
                    meal.center_id = default_center.id
                    meals_updated += 1
            
            if meals_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {meals_updated} وجبة")
            else:
                print("ℹ️ جميع الوجبات محدثة بالفعل")
            
            # 9. تحديث أوامر الشراء
            print("\n📦 تحديث أوامر الشراء...")
            po_updated = 0
            
            for po in PurchaseOrder.query.all():
                if po.center_id is None:
                    po.center_id = default_center.id
                    po_updated += 1
            
            if po_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {po_updated} أمر شراء")
            else:
                print("ℹ️ جميع أوامر الشراء محدثة بالفعل")
            
            # 10. تحديث تسجيلات الأصول
            print("\n🏷️ تحديث تسجيلات الأصول...")
            assets_updated = 0
            
            for asset in AssetRegistration.query.all():
                if asset.center_id is None:
                    asset.center_id = default_center.id
                    assets_updated += 1
            
            if assets_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {assets_updated} أصل")
            else:
                print("ℹ️ جميع الأصول محدثة بالفعل")
            
            # 11. تحديث سجل النشاطات
            print("\n📝 تحديث سجل النشاطات...")
            activity_updated = 0
            
            for activity in ActivityLog.query.all():
                if activity.center_id is None and activity.user_id:
                    user = User.query.get(activity.user_id)
                    if user and user.center_id:
                        activity.center_id = user.center_id
                        activity_updated += 1
            
            if activity_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {activity_updated} نشاط")
            else:
                print("ℹ️ جميع الأنشطة محدثة بالفعل")
            
            # 12. تحديث الصلاحيات
            print("\n🔐 تحديث الصلاحيات...")
            perms_updated = 0
            
            for perm in UserPermission.query.all():
                if perm.center_id is None:
                    user = User.query.get(perm.user_id)
                    if user:
                        perm.center_id = user.center_id
                        perms_updated += 1
            
            if perms_updated > 0:
                db.session.commit()
                print(f"✅ تم تحديث {perms_updated} صلاحية")
            else:
                print("ℹ️ جميع الصلاحيات محدثة بالفعل")
            
            print("\n" + "=" * 80)
            print("✅ تم إكمال الترحيل بنجاح!")
            print("=" * 80)
            print("\n📝 ملخص الترحيل:")
            print(f"   • عدد المراكز: {VocationalCenter.query.count()}")
            print(f"   • عدد المستخدمين: {User.query.count()}")
            print(f"   • عدد الأصناف: {Item.query.count()}")
            print(f"   • عدد الموردين: {Supplier.query.count()}")
            print(f"   • عدد الوصفات: {Recipe.query.count()}")
            print("=" * 80)
            
            return True
        
        except Exception as e:
            print(f"\n❌ خطأ أثناء الترحيل: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = migrate_to_multitenant()
    sys.exit(0 if success else 1)