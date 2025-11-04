from models import User
from app import create_app

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='ALFA').first()
    if user:
        print(f"Username: {user.username}")
        print(f"Password hash: {user.password_hash}")
        
        # Try to verify with different passwords
        test_passwords = ['alfa', 'ALFA', '123456', 'password']
        for pwd in test_passwords:
            result = user.check_password(pwd)
            print(f"  Password '{pwd}': {result}")