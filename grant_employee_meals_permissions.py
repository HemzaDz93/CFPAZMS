#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
منح صلاحيات وجبات الموظفين للمستخدمين
Grant Employee Meals Permissions to Users
"""

import os
import sys
from datetime import datetime

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, UserPermission
from permissions_config import PERMISSIONS

def grant_employee_meals_permissions(username="admin"):
    """منح صلاحيات وجبات الموظفين للمستخدم"""
    
    with app.app_context():
        # البحث عن المستخدم
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ المستخدم '{username}' غير موجود")
            return False
        
        print(f"✓ تم العثور على المستخدم: {user.full_name} ({username})")
        
        # الصلاحيات المراد منحها
        employee_meal_permissions = [
            'restaurant_view_employee_meals',
            'restaurant_add_employee_meal',
            'restaurant_edit_employee_meal',
            'restaurant_view_employee_alerts',
            'restaurant_view_employee_receipt',
        ]
        
        # منح الصلاحيات
        granted_count = 0
        for perm_key in employee_meal_permissions:
            # البحث عن الصلاحية
            perm_data = PERMISSIONS.get('restaurant', {}).get('permissions', {}).get(perm_key)
            if not perm_data:
                print(f"⚠ تحذير: الصلاحية '{perm_key}' غير موجودة في التكوين")
                continue
            
            # البحث عن سجل الصلاحية الموجود أو إنشاء واحد جديد
            user_perm = UserPermission.query.filter_by(
                user_id=user.id,
                permission_key=perm_key
            ).first()
            
            if user_perm:
                # تحديث الصلاحية الموجودة
                if not user_perm.is_allowed:
                    user_perm.is_allowed = True
                    user_perm.updated_at = datetime.utcnow()
                    print(f"  ✓ تم تحديث: {perm_key}")
                    granted_count += 1
                else:
                    print(f"  ℹ موجودة مسبقاً: {perm_key}")
            else:
                # إنشاء صلاحية جديدة
                user_perm = UserPermission(
                    user_id=user.id,
                    permission_key=perm_key,
                    permission_name=perm_data,
                    permission_category='restaurant',
                    is_allowed=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(user_perm)
                print(f"  ✓ تمت إضافة: {perm_key}")
                granted_count += 1
        
        # حفظ التغييرات
        try:
            db.session.commit()
            print(f"\n✅ تم منح {granted_count} صلاحية بنجاح لـ {user.full_name}")
            
            # عرض الصلاحيات الممنوحة
            print(f"\n📋 الصلاحيات الممنوحة:")
            for perm_key in employee_meal_permissions:
                perm_desc = PERMISSIONS.get('restaurant', {}).get('permissions', {}).get(perm_key, 'N/A')
                print(f"  • {perm_key}: {perm_desc}")
            
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ عند حفظ التغييرات: {str(e)}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("منح صلاحيات وجبات الموظفين")
    print("Grant Employee Meals Permissions")
    print("=" * 60)
    print()
    
    # إنشاء التطبيق
    app = create_app()
    
    # منح الصلاحيات للمسؤول
    success = grant_employee_meals_permissions("admin")
    
    if success:
        print("\n✅ اكتملت العملية بنجاح!")
    else:
        print("\n❌ فشلت العملية!")
        sys.exit(1)