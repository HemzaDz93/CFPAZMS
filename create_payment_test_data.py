#!/usr/bin/env python
"""Create test data for employee meal payment testing"""

import sys
from datetime import datetime, timedelta
from app import create_app
from models import db, User, EmployeeMealTransaction, MealRecord, Recipe, UserRole

app = create_app()

with app.app_context():
    # Create or get admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("Error: Admin user not found. Please run init_db first.")
        sys.exit(1)
    
    # Create or get a test recipe
    test_recipe = Recipe.query.filter_by(code='TEST-RECIPE').first()
    if not test_recipe:
        test_recipe = Recipe(
            code='TEST-RECIPE',
            name='وجبة اختبار',
            description='وجبة تجريبية لاختبار دفعات الموظفين',
            servings=1,
            is_active=True
        )
        db.session.add(test_recipe)
        db.session.commit()
        print("✓ Created test recipe")
    
    # Create a test employee if not exists
    test_employee = User.query.filter_by(username='test_employee').first()
    if not test_employee:
        test_employee = User(
            username='test_employee',
            email='test@example.com',
            first_name='موظف',
            last_name='اختبار',
            role=UserRole.WORKER
        )
        test_employee.set_password('password')
        db.session.add(test_employee)
        db.session.commit()
        print("✓ Created test employee: test_employee")
    
    # Create unsettled transactions with valid MealRecord references
    today = datetime.now().date()
    count = 0
    for i in range(3):
        transaction_date = today - timedelta(days=i)
        
        # Check if meal record exists for this date
        meal_record = MealRecord.query.filter_by(
            record_date=transaction_date,
            recipe_id=test_recipe.id
        ).first()
        
        # Create meal record if it doesn't exist
        if not meal_record:
            meal_record = MealRecord(
                record_date=transaction_date,
                meal_type='lunch',
                recipe_id=test_recipe.id,
                servings=1,
                expected_cost=2.5,
                notes=f'وجبة تجريبية {i+1}'
            )
            db.session.add(meal_record)
            db.session.commit()
        
        # Check if transaction already exists
        existing = EmployeeMealTransaction.query.filter_by(
            user_id=test_employee.id,
            meal_record_id=meal_record.id,
            is_settled=False
        ).first()
        
        if not existing:
            transaction = EmployeeMealTransaction(
                user_id=test_employee.id,
                meal_record_id=meal_record.id,
                transaction_date=transaction_date,
                meal_cost=2.5,
                discount_percentage=0,
                discount_amount=0,
                final_cost=2.5,
                payment_method='cash',
                is_settled=False,
                notes=f'وجبة تجريبية {i+1}'
            )
            db.session.add(transaction)
            db.session.commit()
            count += 1
            print(f"✓ Created transaction {transaction.id} for {transaction_date} with meal_record {meal_record.id}")
    
    if count > 0:
        print(f"\n✓ Successfully created {count} unsettled payment transactions")
        print(f"Test employee ID: {test_employee.id}")
        print("You can now test the payment button on /employee-meals/payments")
    else:
        print("Transactions already exist in database")