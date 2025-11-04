#!/usr/bin/env python
"""Create fresh test payment data - clear old and create unsettled transactions"""

from app import create_app
from models import db, User, EmployeeMealTransaction, MealRecord, Recipe, OrganizationSettings
from datetime import datetime, timedelta

def create_fresh_test_data():
    app = create_app()
    
    with app.app_context():
        # Clear all existing transactions
        print("Clearing existing transactions...")
        EmployeeMealTransaction.query.delete()
        db.session.commit()
        
        # Get an existing employee user (not admin)
        employee = User.query.filter(User.username != 'admin').first()
        if not employee:
            print("No employee user found. Creating one...")
            employee = User(
                username='employee_test',
                email='employee_test@test.com',
                first_name='موظف',
                last_name='الاختبار',
                is_active=True
            )
            employee.set_password('password123')
            db.session.add(employee)
            db.session.flush()
        
        print(f"Using employee: {employee.full_name}")
        
        # Check if a recipe exists, if not create one
        recipe = Recipe.query.first()
        if not recipe:
            print("No recipe found. Creating one...")
            recipe = Recipe(
                name='وجبة اختبار',
                name_en='Test Meal',
                meal_type='غداء',
                serving_size=1,
                estimated_cost=2.5
            )
            db.session.add(recipe)
            db.session.flush()
        
        print(f"Using recipe: {recipe.name}")
        
        # Create a meal record for today
        today = datetime.now().date()
        meal_record = MealRecord.query.filter_by(
            record_date=today,
            meal_type='daily'
        ).first()
        
        if not meal_record:
            print(f"Creating meal record for {today}...")
            meal_record = MealRecord(
                record_date=today,
                meal_type='daily',
                recipe_id=recipe.id,
                servings=1,
                expected_cost=2.5,
                notes='سجل وجبات اختبار'
            )
            db.session.add(meal_record)
            db.session.flush()
        
        # Create test transactions (UNSETTLED ONLY)
        print("\nCreating fresh UNSETTLED test transactions...")
        for i in range(3):
            trans_date = datetime.now() - timedelta(days=i)
            transaction = EmployeeMealTransaction(
                user_id=employee.id,
                meal_record_id=meal_record.id,
                transaction_date=trans_date,
                meal_cost=2.5,
                discount_percentage=0,
                discount_amount=0,
                final_cost=2.5,
                payment_method='deferred',
                is_settled=False,  # IMPORTANT: NOT SETTLED
                notes=f'وجبة اختبار {i+1}'
            )
            db.session.add(transaction)
            print(f"  Created transaction {i+1}: 2.5 دج (UNSETTLED)")
        
        db.session.commit()
        
        # Verify
        print("\n" + "="*50)
        unsettled_count = EmployeeMealTransaction.query.filter_by(is_settled=False).count()
        settled_count = EmployeeMealTransaction.query.filter_by(is_settled=True).count()
        print(f"✅ Test data created successfully!")
        print(f"Employee: {employee.full_name}")
        print(f"Unsettled transactions: {unsettled_count}")
        print(f"Settled transactions: {settled_count}")
        print(f"Total unsettled cost: 7.50 دج (3 transactions × 2.5 دج)")

if __name__ == '__main__':
    create_fresh_test_data()