import sys
sys.path.insert(0, r"d:\Program Files\CfpaZMS")
from app import create_app
from models import db, EmployeeMealTransaction, User

app = create_app()
with app.app_context():
    transactions = EmployeeMealTransaction.query.all()
    print(f"Total transactions: {len(transactions)}")
    for t in transactions[:20]:
        user = User.query.get(t.user_id)
        print(f"  ID: {t.id}, User: {user.full_name if user else 'Unknown'}, Amount: {t.final_cost}, Settled: {t.is_settled}")