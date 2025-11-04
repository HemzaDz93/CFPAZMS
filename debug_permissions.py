#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""تصحيح وإضافة صلاحيات المدير"""
from app import create_app
from models import db, User, UserPermission
from permissions_config import get_all_permissions_flat

app = create_app('development')

with app.app_context():
    # الحصول على جميع الصلاحيات
    all_perms = get_all_permissions_flat()
    
    # التحقق من وجود employee_dashboard_view
    if 'employee_dashboard_view' in all_perms:
        print("✓ تم العثور على الصلاحية: employee_dashboard_view")
        print(f"  الاسم: {all_perms['employee_dashboard_view']['name']}")
        print(f"  الفئة: {all_perms['employee_dashboard_view']['category']}")
    else:
        print("✗ لم يتم العثور على الصلاحية: employee_dashboard_view")
    
    # طباعة جميع صلاحيات Dashboard
    print("\n🔑 جميع صلاحيات Dashboard:")
    for perm_key, perm_info in all_perms.items():
        if 'dashboard' in perm_key.lower():
            print(f"  - {perm_key}: {perm_info['name']} (الفئة: {perm_info['category']})")
    
    # الآن إضافة الصلاحية المفقودة للمدير
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print(f"\n👤 إضافة الصلاحيات المفقودة للمدير...")
        
        # التحقق من الصلاحيات المفقودة
        existing_perms = {p.permission_key for p in admin_user.user_permissions}
        missing_perms = set(all_perms.keys()) - existing_perms
        
        if missing_perms:
            print(f"  تم العثور على {len(missing_perms)} صلاحية مفقودة:")
            for perm_key in sorted(missing_perms):
                perm_info = all_perms[perm_key]
                print(f"    - {perm_key}")
                
                # إضافة الصلاحية
                permission = UserPermission(
                    user_id=admin_user.id,
                    permission_key=perm_key,
                    permission_name=perm_info['name'],
                    permission_category=perm_info['category'],
                    is_allowed=True
                )
                db.session.add(permission)
            
            db.session.commit()
            print(f"\n✓ تمت إضافة {len(missing_perms)} صلاحية بنجاح!")
        else:
            print("  ✓ المدير لديه جميع الصلاحيات!")