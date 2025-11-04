#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""التحقق من صلاحيات المدير وإضافتها إن لزم الأمر"""
import os
import sys
from app import create_app
from models import db, User, UserRole, UserPermission
from permissions_config import get_all_permissions_flat

app = create_app('development')

with app.app_context():
    print("=" * 80)
    print("🔍 التحقق من صلاحيات المدير")
    print("=" * 80)
    
    # البحث عن المدير
    admin_user = User.query.filter_by(username='admin').first()
    
    if not admin_user:
        print("❌ لم يتم العثور على حساب المدير!")
        sys.exit(1)
    
    print(f"✓ تم العثور على حساب المدير: {admin_user.username}")
    print(f"  - البريد الإلكتروني: {admin_user.email}")
    print(f"  - الدور: {admin_user.role}")
    print(f"  - نشط: {admin_user.is_active}")
    
    # التحقق من عدد الصلاحيات الحالية
    current_perms = UserPermission.query.filter_by(user_id=admin_user.id).all()
    print(f"\n📊 عدد الصلاحيات الحالية: {len(current_perms)}")
    
    # الحصول على جميع الصلاحيات المتاحة
    all_perms = get_all_permissions_flat()
    print(f"📋 إجمالي الصلاحيات المتاحة في النظام: {len(all_perms)}")
    
    # التحقق من وجود الصلاحيات المهمة
    important_perms = ['dashboard_view', 'employee_dashboard_view']
    print(f"\n🔑 التحقق من الصلاحيات المهمة:")
    for perm in important_perms:
        has_perm = UserPermission.query.filter_by(
            user_id=admin_user.id,
            permission_key=perm,
            is_allowed=True
        ).first()
        status = "✓" if has_perm else "✗"
        print(f"  {status} {perm}")
    
    # إذا كانت الصلاحيات ناقصة، تم إضافتها
    if len(current_perms) < len(all_perms):
        print(f"\n⚙️  جارٍ إضافة الصلاحيات المفقودة...")
        
        # حذف الصلاحيات القديمة
        UserPermission.query.filter_by(user_id=admin_user.id).delete()
        db.session.commit()
        print("  - تم مسح الصلاحيات القديمة")
        
        # إضافة جميع الصلاحيات الجديدة
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
        print(f"  ✓ تمت إضافة {len(all_perms)} صلاحية للمدير")
        
        # التحقق من الصلاحيات المهمة مرة أخرى
        print(f"\n🔑 إعادة التحقق من الصلاحيات المهمة:")
        for perm in important_perms:
            has_perm = UserPermission.query.filter_by(
                user_id=admin_user.id,
                permission_key=perm,
                is_allowed=True
            ).first()
            status = "✓" if has_perm else "✗"
            print(f"  {status} {perm}")
    else:
        print(f"\n✓ المدير لديه جميع الصلاحيات المطلوبة ({len(current_perms)} صلاحية)")
    
    print("\n" + "=" * 80)
    print("✅ تم التحقق والتصحيح بنجاح!")
    print("=" * 80)