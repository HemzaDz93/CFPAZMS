#!/usr/bin/env python
"""تهيئة قاعدة البيانات"""
import os
from app import create_app
from models import db, User, UserRole, OrganizationSettings, UserPermission
from permissions_config import get_all_permissions_flat

app = create_app('development')

with app.app_context():
    # إنشاء الجداول
    db.create_all()
    print("✓ تم إنشاء الجداول بنجاح")
    
    # إنشاء إعدادات المؤسسة
    if not OrganizationSettings.query.first():
        org = OrganizationSettings(
            ministry_name="وزارة التعليم العالي",
            ministry_name_en="Ministry of Higher Education",
            directorate_name="مديرية التعليم والتكوين",
            directorate_name_en="Directorate of Education and Training",
            institution_name="المؤسسة الوطنية للتعليم",
            institution_name_en="National Educational Institution",
            institution_code="INST001",
            address="الجزائر",
            phone="+213555555555",
            email="info@institution.dz",
            tax_id="123456789"
        )
        db.session.add(org)
        db.session.commit()
        print("✓ تم إنشاء إعدادات المؤسسة بنجاح")
    
    # إنشاء حساب المدير
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@institution.dz',
            first_name='المدير',
            last_name='العام',
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.flush()
        print("✓ تم إنشاء حساب المدير بنجاح")
        print("  اسم المستخدم: admin")
        print("  كلمة المرور: admin123")
    
    # إضافة جميع الصلاحيات للمدير
    if admin_user and UserPermission.query.filter_by(user_id=admin_user.id).count() == 0:
        all_perms = get_all_permissions_flat()
        for perm_key, perm_info in all_perms.items():
            permission = UserPermission(
                user_id=admin_user.id,
                permission_key=perm_key,
                permission_name=perm_info['name'],
                permission_category=perm_info['category'],
                is_allowed=True  # المدير لديه جميع الصلاحيات
            )
            db.session.add(permission)
        db.session.commit()
        print("✓ تم إضافة جميع الصلاحيات لحساب المدير")
    
    print("\n✅ تم تهيئة قاعدة البيانات بنجاح!")
    print("\n📌 ملاحظات مهمة:")
    print("   • صلاحية 'dashboard_view': لوحة التحكم الإدارية (للمديرين)")
    print("   • صلاحية 'employee_dashboard_view': لوحة التحكم الخاصة بالموظفين")
    print("   • الموظفون يحتاجون إلى 'employee_dashboard_view' لعرض لوحة التحكم الخاصة بهم")
    print("   • المديرون يحصلون على كلا الصلاحيتين تلقائياً")