import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, UserPermission, User
from permissions_config import get_all_permissions_flat


def grant_all_to_username(username: str):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"لم يتم العثور على مستخدم باسم '{username}'")
            return 1

        perms = get_all_permissions_flat()
        existing = {p.permission_key: p for p in UserPermission.query.filter_by(user_id=user.id).all()}

        added = 0
        updated = 0
        for key, meta in perms.items():
            if key in existing:
                p = existing[key]
                if not p.is_allowed:
                    p.is_allowed = True
                    updated += 1
            else:
                new = UserPermission(
                    user_id=user.id,
                    permission_key=key,
                    permission_name=meta.get('name', key),
                    permission_category=meta.get('category', 'default'),
                    is_allowed=True
                )
                db.session.add(new)
                added += 1

        db.session.commit()
        total = len(perms)
        print(f"تم منح جميع الصلاحيات للمستخدم '{username}' (مجموع الصلاحيات: {total} — مضافة: {added}, محدثة: {updated})")
        return 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('username', nargs='?', default='admin')
    args = parser.parse_args()
    exit(grant_all_to_username(args.username))
