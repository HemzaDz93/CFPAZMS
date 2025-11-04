from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, current_app
)
from flask_login import login_required, current_user
from models import (
    db, Recipe, RecipeIngredient, MealRecord, Item, 
    Transaction, ActivityLog, ItemCategory
)
from datetime import datetime, date, timedelta
from auth_helpers import require_granular_permission

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

# ==================== Recipes ====================

@restaurant_bp.route('/recipes')
@login_required
def recipes():
    """قائمة الوصفات"""
    # التحقق من صلاحية عرض الوصفات
    if not current_user.has_granular_permission('restaurant_view_recipes'):
        flash('ليس لديك صلاحية لعرض الوصفات', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Recipe.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            (Recipe.code.ilike(f'%{search}%')) |
            (Recipe.name.ilike(f'%{search}%'))
        )
    
    pagination = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    
    return render_template(
        'restaurant/recipes.html',
        recipes=pagination.items,
        pages=pagination.pages,
        current_page=page,
        search=search
    )

@restaurant_bp.route('/recipes/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    """إضافة وصفة جديدة"""
    # التحقق من صلاحية إضافة الوصفات
    if not current_user.has_granular_permission('restaurant_add_recipe'):
        flash('ليس لديك صلاحية لإضافة وصفات', 'danger')
        return redirect(url_for('restaurant.recipes'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()
        
        if not code or not name:
            flash('الكود والاسم مطلوبان', 'warning')
            return redirect(url_for('restaurant.add_recipe'))
        
        if Recipe.query.filter_by(code=code).first():
            flash('هذا الكود موجود بالفعل', 'danger')
            return redirect(url_for('restaurant.add_recipe'))
        
        recipe = Recipe(
            code=code,
            name=name,
            description=request.form.get('description', ''),
            servings=int(request.form.get('servings', 1))
        )
        
        db.session.add(recipe)
        db.session.flush()
        
        # إضافة المكونات
        items = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        for item_id, qty, unit in zip(items, quantities, units):
            if item_id and qty:
                ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    item_id=item_id,
                    quantity=float(qty),
                    unit=unit
                )
                db.session.add(ingredient)
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"إضافة وصفة جديدة: {name}",
            entity_type='Recipe',
            entity_id=recipe.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم إضافة الوصفة بنجاح', 'success')
        return redirect(url_for('restaurant.recipes'))
    
    # Query for food items (items in food category type)
    from models import ItemCategory_Model
    food_category = ItemCategory_Model.query.filter_by(category_type='food_items').first()
    items = []
    if food_category:
        items = Item.query.filter_by(
            is_active=True,
            category_id=food_category.id
        ).all()
    
    return render_template('restaurant/add_recipe.html', items=items)

@restaurant_bp.route('/recipes/edit/<recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    """تعديل وصفة"""
    # التحقق من صلاحية تعديل الوصفات
    if not current_user.has_granular_permission('restaurant_edit_recipe'):
        flash('ليس لديك صلاحية لتعديل الوصفات', 'danger')
        return redirect(url_for('restaurant.recipes'))
    
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if request.method == 'POST':
        recipe.name = request.form.get('name', recipe.name)
        recipe.description = request.form.get('description', recipe.description)
        recipe.servings = int(request.form.get('servings', recipe.servings))
        
        # حذف المكونات القديمة
        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
        
        # إضافة المكونات الجديدة
        items = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        for item_id, qty, unit in zip(items, quantities, units):
            if item_id and qty:
                ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    item_id=item_id,
                    quantity=float(qty),
                    unit=unit
                )
                db.session.add(ingredient)
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"تعديل وصفة: {recipe.name}",
            entity_type='Recipe',
            entity_id=recipe.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تحديث الوصفة بنجاح', 'success')
        return redirect(url_for('restaurant.recipes'))
    
    items = Item.query.filter_by(is_active=True).all()
    return render_template('restaurant/edit_recipe.html', recipe=recipe, items=items)

# ==================== Meals ====================

@restaurant_bp.route('/meals')
@login_required
def meals():
    """سجل الوجبات"""
    # التحقق من صلاحية عرض الوجبات
    if not current_user.has_granular_permission('restaurant_view_meals'):
        flash('ليس لديك صلاحية لعرض الوجبات', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    meal_date = request.args.get('date', date.today().isoformat())
    
    try:
        meal_date_obj = datetime.strptime(meal_date, '%Y-%m-%d').date()
    except ValueError:
        meal_date_obj = date.today()
    
    pagination = MealRecord.query.filter_by(
        record_date=meal_date_obj
    ).paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    
    # Calculate daily summary statistics
    all_meals = MealRecord.query.filter_by(record_date=meal_date_obj).all()
    breakfast_count = sum(1 for m in all_meals if m.meal_type == 'breakfast')
    lunch_count = sum(1 for m in all_meals if m.meal_type == 'lunch')
    dinner_count = sum(1 for m in all_meals if m.meal_type == 'dinner')
    total_cost = sum(m.expected_cost or 0 for m in all_meals)
    
    return render_template(
        'restaurant/meals.html',
        meals=pagination.items,
        pages=pagination.pages,
        current_page=page,
        meal_date=meal_date_obj.isoformat(),
        breakfast_count=breakfast_count,
        lunch_count=lunch_count,
        dinner_count=dinner_count,
        total_cost=total_cost
    )

@restaurant_bp.route('/meals/add', methods=['GET', 'POST'])
@login_required
def add_meal():
    """إضافة وجبة"""
    # التحقق من صلاحية إضافة الوجبات
    if not current_user.has_granular_permission('restaurant_add_meal'):
        flash('ليس لديك صلاحية لإضافة وجبات', 'danger')
        return redirect(url_for('restaurant.meals'))
    
    if request.method == 'POST':
        recipe_id = request.form.get('recipe_id', '')
        meal_type = request.form.get('meal_type', '')
        servings = int(request.form.get('servings', 1))
        
        if not recipe_id or not meal_type:
            flash('جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('restaurant.add_meal'))
        
        recipe = Recipe.query.get_or_404(recipe_id)
        
        # Parse meal_date from datetime-local format (YYYY-MM-DDTHH:mm)
        meal_date_str = request.form.get('meal_date', date.today().isoformat() + 'T00:00')
        try:
            meal_date_obj = datetime.fromisoformat(meal_date_str).date()
        except (ValueError, AttributeError):
            meal_date_obj = date.today()
        
        # Calculate expected cost based on ingredients
        expected_cost = 0
        for ingredient in recipe.ingredients:
            quantity_needed = ingredient.quantity * servings / recipe.servings
            ingredient_cost = quantity_needed * (ingredient.item.unit_price or 0)
            expected_cost += ingredient_cost
        
        meal = MealRecord(
            record_date=meal_date_obj,
            meal_type=meal_type,
            recipe_id=recipe_id,
            servings=servings,
            expected_cost=expected_cost,
            notes=request.form.get('notes', '')
        )
        
        db.session.add(meal)
        db.session.flush()
        
        # تحديث المخزون بناءً على الوصفة
        for ingredient in recipe.ingredients:
            quantity_needed = ingredient.quantity * servings / recipe.servings
            
            # تسجيل عملية استخراج
            transaction = Transaction(
                reference_number=f"MEAL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                transaction_type='issue',
                item_id=ingredient.item_id,
                quantity=quantity_needed,
                unit_price=ingredient.item.unit_price,
                total_value=quantity_needed * (ingredient.item.unit_price or 0),
                created_by_id=current_user.id,
                description=f"استهلاك - وجبة: {recipe.name}"
            )
            
            # تحديث المخزون
            ingredient.item.quantity_in_stock -= quantity_needed
            
            db.session.add(transaction)
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"إضافة وجبة: {recipe.name} - {meal_type}",
            entity_type='MealRecord',
            entity_id=meal.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تسجيل الوجبة بنجاح وتحديث المخزون', 'success')
        return redirect(url_for('restaurant.meals'))
    
    recipes = Recipe.query.filter_by(is_active=True).all()
    return render_template('restaurant/add_meal.html', recipes=recipes)

# ==================== Daily Report ====================

@restaurant_bp.route('/daily-report')
@login_required
def daily_report():
    """التقرير اليومي"""
    # التحقق من صلاحية عرض تقارير المطعم
    if not current_user.has_granular_permission('restaurant_view_meals'):
        flash('ليس لديك صلاحية لعرض تقارير المطعم', 'danger')
        return redirect(url_for('dashboard.index'))
    
    meal_date = request.args.get('date', date.today().isoformat())
    
    try:
        meal_date_obj = datetime.strptime(meal_date, '%Y-%m-%d').date()
    except ValueError:
        meal_date_obj = date.today()
    
    meals = MealRecord.query.filter_by(record_date=meal_date_obj).all()
    
    total_consumption = {}
    for meal in meals:
        for ingredient in meal.recipe.ingredients:
            qty_needed = ingredient.quantity * meal.servings / meal.recipe.servings
            
            if ingredient.item_id not in total_consumption:
                total_consumption[ingredient.item_id] = {
                    'item': ingredient.item,
                    'quantity': 0,
                    'unit': ingredient.unit
                }
            
            total_consumption[ingredient.item_id]['quantity'] += qty_needed
    
    return render_template(
        'restaurant/daily_report.html',
        meals=meals,
        total_consumption=total_consumption.values(),
        meal_date=meal_date_obj
    )