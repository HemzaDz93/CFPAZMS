from models import User
from app import create_app

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='ALFA').first()
    if user:
        print(f"Username: {user.username}, Role: {user.role}")
        # Check admin permissions
        admin_perms = [
            'admin_view_users',
            'admin_add_user',
            'admin_edit_user',
            'admin_delete_user',
            'admin_manage_permissions',
            'admin_view_activity_logs',
            'admin_manage_organization_settings'
        ]
        for perm in admin_perms:
            has_it = user.has_granular_permission(perm)
            print(f"  {perm}: {has_it}")