#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""سكريبت لإعطاء جميع الصلاحيات لمسؤول النظام"""

import sys
from app import create_app
from models import db, User, UserPermission
from permissions_config import get_all_permissions_flat

def grant_all_permissions():
    """إعطاء جميع الصلاحيات لمستخدم المسؤول"""
    app = create_app()
    with app.app_context():
        # البحث عن المستخدم
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("[ERROR] لم يتم العثور على مستخدم بالاسم 'admin'")
            sys.exit(1)
        
        print(f"[INFO] جاري إعطاء الصلاحيات للمستخدم: {admin_user.username} ({admin_user.full_name})")
        
        # الحصول على جميع الصلاحيات
        all_permissions = get_all_permissions_flat()
        
        # إضافة أو تحديث كل صلاحية
        added_count = 0
        updated_count = 0
        
        for perm_key, perm_data in all_permissions.items():
            # البحث عن الصلاحية الموجودة
            user_perm = UserPermission.query.filter_by(
                user_id=admin_user.id,
                permission_key=perm_key
            ).first()
            
            if user_perm:
                # تحديث الصلاحية الموجودة
                if not user_perm.is_allowed:
                    user_perm.is_allowed = True
                    updated_count += 1
                    print(f"  ✓ تحديث: {perm_key} ({perm_data['name']})")
            else:
                # إضافة صلاحية جديدة
                user_perm = UserPermission(
                    user_id=admin_user.id,
                    permission_key=perm_key,
                    permission_name=perm_data['name'],
                    permission_category=perm_data['category'],
                    is_allowed=True
                )
                db.session.add(user_perm)
                added_count += 1
                print(f"  + إضافة: {perm_key} ({perm_data['name']})")
        
        # حفظ التغييرات
        db.session.commit()
        
        print(f"\n[SUCCESS] تم بنجاح:")
        print(f"  - عدد الصلاحيات الجديدة المضافة: {added_count}")
        print(f"  - عدد الصلاحيات المحدثة: {updated_count}")
        print(f"  - إجمالي الصلاحيات: {added_count + updated_count}")
        print(f"\n[INFO] المستخدم '{admin_user.username}' الآن لديه جميع صلاحيات النظام")

if __name__ == '__main__':
    grant_all_permissions()