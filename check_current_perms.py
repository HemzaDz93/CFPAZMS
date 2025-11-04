#!/usr/bin/env python
"""Check current user permissions"""
from app import create_app
from models import db, User, UserPermission

app = create_app('development')
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f'Admin User Found: {admin.username}')
        print(f'Admin ID: {admin.id}')
        print(f'Has dashboard_view: {admin.has_granular_permission("dashboard_view")}')
        print(f'Has employee_dashboard_view: {admin.has_granular_permission("employee_dashboard_view")}')
        
        perms = UserPermission.query.filter_by(user_id=admin.id).all()
        print(f'\nTotal permissions assigned: {len(perms)}')
        
        # Check specifically for these
        dashboard_perm = UserPermission.query.filter_by(user_id=admin.id, permission_key='dashboard_view').first()
        emp_perm = UserPermission.query.filter_by(user_id=admin.id, permission_key='employee_dashboard_view').first()
        
        if dashboard_perm:
            print(f'✓ dashboard_view found: {dashboard_perm.permission_name}')
        else:
            print('✗ dashboard_view NOT found')
            
        if emp_perm:
            print(f'✓ employee_dashboard_view found: {emp_perm.permission_name}')
        else:
            print('✗ employee_dashboard_view NOT found')
    else:
        print('No admin user found')