# -*- coding: utf-8 -*-
"""
نماذج نظام مراكز التكوين المهني
Vocational Training Center System Models
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# يتم استيراد db من models.py الرئيسي
# from models import db

def register_vocational_models(db):
    """تسجيل نماذج مراكز التكوين مع قاعدة البيانات"""
    
    class VocationalCenter(db.Model):
        """نموذج مركز التكوين المهني"""
        __tablename__ = 'vocational_centers'
        
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        
        # معلومات المركز
        code = db.Column(db.String(50), unique=True, nullable=False, index=True)
        name_ar = db.Column(db.String(255), nullable=False)
        name_en = db.Column(db.String(255), nullable=True)
        
        # معلومات التنظيم
        ministry_name = db.Column(db.String(255), nullable=False, default="وزارة التكوين المهني")
        directorate_name = db.Column(db.String(255), nullable=False, default="المديرية")
        
        # معلومات الاتصال
        phone = db.Column(db.String(20), nullable=True)
        email = db.Column(db.String(120), nullable=True)
        address = db.Column(db.Text, nullable=True)
        
        # الإدارة
        manager_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
        supervisor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
        
        # التخصص والقدرة
        specialization = db.Column(db.String(255), nullable=True)
        capacity = db.Column(db.Integer, default=0)
        budget_allocation = db.Column(db.Float, nullable=True)
        
        # الحالة
        status = db.Column(db.String(50), default='active')  # active, inactive, under_maintenance
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<VocationalCenter {self.name_ar}>'
    
    
    class TrainingProgram(db.Model):
        """نموذج البرنامج التدريبي"""
        __tablename__ = 'training_programs'
        
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        center_id = db.Column(db.String(36), db.ForeignKey('vocational_centers.id'), nullable=False, index=True)
        
        # معلومات البرنامج
        code = db.Column(db.String(50), unique=True, nullable=False)
        name_ar = db.Column(db.String(255), nullable=False)
        name_en = db.Column(db.String(255), nullable=True)
        description = db.Column(db.Text, nullable=True)
        
        # تفاصيل التدريب
        duration_hours = db.Column(db.Integer, nullable=False)
        duration_months = db.Column(db.Integer, nullable=True)
        level = db.Column(db.String(50), default='basic')  # basic, intermediate, advanced
        
        # المعلومات الإدارية
        instructor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
        max_trainees = db.Column(db.Integer, default=30)
        current_trainees = db.Column(db.Integer, default=0)
        
        # التواريخ
        start_date = db.Column(db.DateTime, nullable=True)
        end_date = db.Column(db.DateTime, nullable=True)
        
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<TrainingProgram {self.name_ar}>'
    
    
    class Trainee(db.Model):
        """نموذج المتدرب"""
        __tablename__ = 'trainees'
        
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        center_id = db.Column(db.String(36), db.ForeignKey('vocational_centers.id'), nullable=False, index=True)
        program_id = db.Column(db.String(36), db.ForeignKey('training_programs.id'), nullable=False, index=True)
        
        # معلومات المتدرب
        first_name = db.Column(db.String(100), nullable=False)
        last_name = db.Column(db.String(100), nullable=False)
        national_id = db.Column(db.String(50), unique=True, nullable=True)
        email = db.Column(db.String(120), nullable=True)
        phone = db.Column(db.String(20), nullable=True)
        
        # معلومات التسجيل
        enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
        graduation_date = db.Column(db.DateTime, nullable=True)
        
        # الحالة
        status = db.Column(db.String(50), default='enrolled')  # enrolled, active, graduated, dropped_out
        notes = db.Column(db.Text, nullable=True)
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<Trainee {self.first_name} {self.last_name}>'
        
        @property
        def full_name(self):
            return f"{self.first_name} {self.last_name}"
    
    
    class EquipmentTransferRequest(db.Model):
        """نموذج طلب نقل المعدات بين مراكز التكوين"""
        __tablename__ = 'equipment_transfer_requests'
        
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        
        # المراكز
        from_center_id = db.Column(db.String(36), db.ForeignKey('vocational_centers.id'), nullable=False, index=True)
        to_center_id = db.Column(db.String(36), db.ForeignKey('vocational_centers.id'), nullable=False, index=True)
        
        # المادة/المعدة
        item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
        quantity = db.Column(db.Float, nullable=False)
        
        # السبب والأولوية
        reason = db.Column(db.Text, nullable=False)
        priority = db.Column(db.String(50), default='normal')  # urgent, normal, low
        
        # طالب الطلب
        requested_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
        requested_date = db.Column(db.DateTime, default=datetime.utcnow)
        
        # مراحل الموافقة
        from_manager_approval = db.Column(db.String(50), default='pending')
        from_manager_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
        from_manager_date = db.Column(db.DateTime, nullable=True)
        from_manager_notes = db.Column(db.Text, nullable=True)
        
        to_manager_approval = db.Column(db.String(50), default='pending')
        to_manager_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
        to_manager_date = db.Column(db.DateTime, nullable=True)
        to_manager_notes = db.Column(db.Text, nullable=True)
        
        founder_approval = db.Column(db.String(50), default='pending')
        founder_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
        founder_date = db.Column(db.DateTime, nullable=True)
        founder_notes = db.Column(db.Text, nullable=True)
        
        # الحالة النهائية
        status = db.Column(db.String(50), default='pending')  # pending, approved, rejected, completed
        rejection_reason = db.Column(db.Text, nullable=True)
        
        # تنفيذ النقل
        transfer_date = db.Column(db.DateTime, nullable=True)
        transferred_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
        transfer_notes = db.Column(db.Text, nullable=True)
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<EquipmentTransferRequest {self.id}>'
    
    
    class MaintenanceLog(db.Model):
        """نموذج سجل صيانة المعدات"""
        __tablename__ = 'maintenance_logs'
        
        id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        
        center_id = db.Column(db.String(36), db.ForeignKey('vocational_centers.id'), nullable=False, index=True)
        item_id = db.Column(db.String(36), db.ForeignKey('items.id'), nullable=False)
        
        # نوع الصيانة
        maintenance_type = db.Column(db.String(50), nullable=False)  # preventive, corrective, emergency
        description = db.Column(db.Text, nullable=False)
        performed_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
        
        # التواريخ
        maintenance_date = db.Column(db.DateTime, default=datetime.utcnow)
        next_maintenance_date = db.Column(db.DateTime, nullable=True)
        
        # التكلفة والحالة
        cost = db.Column(db.Float, nullable=True)
        notes = db.Column(db.Text, nullable=True)
        status = db.Column(db.String(50), default='completed')  # scheduled, in_progress, completed, pending
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def __repr__(self):
            return f'<MaintenanceLog {self.id}>'
    
    
    return {
        'VocationalCenter': VocationalCenter,
        'TrainingProgram': TrainingProgram,
        'Trainee': Trainee,
        'EquipmentTransferRequest': EquipmentTransferRequest,
        'MaintenanceLog': MaintenanceLog,
    }