#!/usr/bin/env python
"""Initialize default recipe for employee meal system"""

import sys
sys.path.insert(0, 'd:\\Program Files\\CfpaZMS')

from app import create_app
from models import db, Recipe
from datetime import datetime
import uuid

# Create app with development config
app = create_app('development')

with app.app_context():
    # Check if a default recipe already exists
    default_recipe = Recipe.query.filter_by(name='وجبة يومية').first()
    
    if not default_recipe:
        # Create a default recipe for daily meals
        recipe = Recipe(
            code='DAILY_MEAL_001',
            name='وجبة يومية',
            description='وجبة يومية افتراضية لتسجيل استهلاك الموظفين',
            servings=1,
            is_active=True
        )
        
        db.session.add(recipe)
        db.session.commit()
        print(f'[OK] Default recipe created: {recipe.id} - {recipe.name}')
    else:
        print(f'[OK] Default recipe already exists: {default_recipe.id} - {default_recipe.name}')