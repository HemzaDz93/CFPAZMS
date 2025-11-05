import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, OrganizationSettings, User
from models import UserRole

app = create_app()

with app.app_context():
    db.create_all()

    if not OrganizationSettings.query.first():
        org = OrganizationSettings(
            ministry_name="الوزارة ",
            directorate_name="المديرية ",
            institution_name="المؤسسة ",
            institution_code="INST001",
            address="العنوان",
            phone="+213555555555",
            email="info@institution.dz",
            tax_id="123456789"
        )
        db.session.add(org)
        db.session.commit()
        print("تم إنشاء إعدادات المؤسسة بنجاح")

    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='benselilih.messaoud@gmail.com',
            first_name='بن سليليح',
            last_name='المسعود',
            role=UserRole.ADMIN,
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("تم إنشاء حساب المدير بنجاح - اسم المستخدم: admin - كلمة المرور: admin123")

    print('تهيئة قاعدة البيانات اكتملت.')
