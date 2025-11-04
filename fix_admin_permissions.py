#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""إصلاح وإضافة جميع الصلاحيات للمدير"""
from app import create_app
from models import db, User, UserPermission
from permissions_config import get_all_permissions_flat

app = create_app('development')

with app.app_context():
    print("=" * 80)
    print("🔧 إصلاح صلاحيات المدير")
    print("=" * 80)
    
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("❌ لم يتم العثور على المدير!")
        exit(1)
    
    # الحصول على جميع الصلاحيات
    all_perms = get_all_permissions_flat()
    print(f"📋 إجمالي الصلاحيات: {len(all_perms)}")
    
    # حذف جميع صلاحيات المدير الحالية
    old_count = UserPermission.query.filter_by(user_id=admin_user.id).count()
    UserPermission.query.filter_by(user_id=admin_user.id).delete()
    db.session.commit()
    print(f"🗑️  تم حذف {old_count} صلاحية قديمة")
    
    # إضافة جميع الصلاحيات الجديدة
    print(f"⚙️  جاري إضافة {len(all_perms)} صلاحية جديدة...")
    for perm_key, perm_info in all_perms.items():
        permission = UserPermission(
            user_id=admin_user.id,
            permission_key=perm_key,
            permission_name=perm_info['name'],
            permission_category=perm_info['category'],
            is_allowed=True
        )
        db.session.add(permission)
    
    db.session.commit()
    print(f"✅ تمت إضافة جميع الصلاحيات بنجاح!")
    
    # التحقق من النتيجة
    print(f"\n🔍 التحقق من الصلاحيات المهمة:")
    important_perms = ['dashboard_view', 'employee_dashboard_view', 'admin_view_users']
    for perm_key in important_perms:
        has_perm = UserPermission.query.filter_by(
            user_id=admin_user.id,
            permission_key=perm_key,
            is_allowed=True
        ).first()
        status = "✓" if has_perm else "✗"
        print(f"  {status} {perm_key}")
    
    # الإحصائيات النهائية
    final_count = UserPermission.query.filter_by(user_id=admin_user.id, is_allowed=True).count()
    print(f"\n📊 الإحصائيات:")
    print(f"  - عدد صلاحيات المدير الآن: {final_count}")
    print(f"  - عدد الصلاحيات المتاحة في النظام: {len(all_perms)}")
    print(f"  - الحالة: {'✅ متطابقة' if final_count == len(all_perms) else '⚠️ غير متطابقة'}")
    
    print("\n" + "=" * 80)
    print("✅ تم إصلاح الصلاحيات بنجاح!")
    print("=" * 80)