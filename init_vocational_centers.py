#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Initialize Vocational Training Centers System
"""

import sys
import os

# Set encoding for output
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import create_app, db
from models import (
    User, UserRole, VocationalCenter, TrainingProgram, 
    Trainee, EquipmentTransferRequest, MaintenanceLog
)

def init_database():
    """Initialize database tables"""
    app = create_app()
    
    with app.app_context():
        print("[*] Creating database tables...")
        db.create_all()
        print("[+] Database tables created successfully")
        
        return True


def create_sample_founder():
    """Create founder account"""
    app = create_app()
    
    with app.app_context():
        print("\n[*] Creating founder account...")
        
        founder = User.query.filter_by(username='founder').first()
        if founder:
            print("[i] Founder account already exists")
            return founder
        
        founder = User(
            username='founder',
            email='founder@vocational-training.dz',
            first_name='Admin',
            last_name='Founder',
            role=UserRole.FOUNDER,
            is_active=True,
            is_verified=True,
            center_id=None
        )
        founder.set_password('founder123')
        
        db.session.add(founder)
        db.session.commit()
        
        print("[+] Founder account created: founder / founder123")
        return founder


def create_sample_centers():
    """Create sample vocational training centers"""
    app = create_app()
    
    with app.app_context():
        print("\n[*] Creating vocational training centers...")
        
        centers_data = [
            {
                'code': 'VTC-001',
                'name_ar': 'Mechanics Center',
                'name_en': 'Mechanics Training Center',
                'specialization': 'Mechanics',
                'capacity': 100,
                'budget_allocation': 500000.00
            },
            {
                'code': 'VTC-002',
                'name_ar': 'Electrical Center',
                'name_en': 'Electrical Training Center',
                'specialization': 'Electricity',
                'capacity': 80,
                'budget_allocation': 450000.00
            },
            {
                'code': 'VTC-003',
                'name_ar': 'Electronics Center',
                'name_en': 'Electronics Training Center',
                'specialization': 'Electronics',
                'capacity': 60,
                'budget_allocation': 400000.00
            },
            {
                'code': 'VTC-004',
                'name_ar': 'Construction Center',
                'name_en': 'Construction Training Center',
                'specialization': 'Building & Construction',
                'capacity': 90,
                'budget_allocation': 480000.00
            }
        ]
        
        for center_data in centers_data:
            existing = VocationalCenter.query.filter_by(code=center_data['code']).first()
            if existing:
                print("[i] Center already exists: {}".format(center_data['code']))
                continue
            
            center = VocationalCenter(**center_data)
            db.session.add(center)
        
        db.session.commit()
        print("[+] Vocational training centers created")
        
        return VocationalCenter.query.all()


def create_sample_center_managers(centers):
    """Create center managers"""
    app = create_app()
    
    with app.app_context():
        print("\n[*] Creating center managers...")
        
        managers_data = [
            {'name': 'Ahmed Mohamed', 'center_index': 0},
            {'name': 'Fatima Ali', 'center_index': 1},
            {'name': 'Khalid Nour', 'center_index': 2},
            {'name': 'Layla Sarah', 'center_index': 3}
        ]
        
        for mgr_data in managers_data:
            username = "manager_{}".format(mgr_data['center_index'])
            
            existing = User.query.filter_by(username=username).first()
            if existing:
                center = centers[mgr_data['center_index']]
                center.manager_id = existing.id
                db.session.commit()
                continue
            
            center = centers[mgr_data['center_index']]
            
            manager = User(
                username=username,
                email="{}@vocational-training.dz".format(username),
                first_name=mgr_data['name'].split()[0],
                last_name=mgr_data['name'].split()[1] if len(mgr_data['name'].split()) > 1 else '',
                role=UserRole.CENTER_MANAGER,
                center_id=center.id,
                is_active=True,
                is_verified=True,
                position='Center Manager'
            )
            manager.set_password('manager123')
            
            db.session.add(manager)
            center.manager_id = manager.id
            
        db.session.commit()
        print("[+] Center managers created")


def main():
    """Run initialization"""
    print("=" * 60)
    print("Initializing Vocational Training Centers System")
    print("=" * 60)
    
    try:
        init_database()
        founder = create_sample_founder()
        centers = create_sample_centers()
        create_sample_center_managers(centers)
        
        print("\n" + "=" * 60)
        print("[+] Initialization completed successfully!")
        print("=" * 60)
        print("\nLogin Credentials:")
        print("  Founder Account:")
        print("    Username: founder")
        print("    Password: founder123")
        print("\n  Center Manager Accounts:")
        for i in range(4):
            print("    Username: manager_{}".format(i))
            print("    Password: manager123")
        
        return 0
        
    except Exception as e:
        print("\n[-] Error: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())