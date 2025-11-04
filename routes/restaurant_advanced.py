from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, current_app, jsonify
)
from flask_login import login_required, current_user
from models import (
    db, FoodWaste, WasteAnalysis, DemandForecast, DemandAnalysis,
    EmployeeMealSubsidy, EmployeeMealTransaction, MealPayrollIntegration,
    MealRecord, Recipe, User, Item, ActivityLog
)
from datetime import datetime, date, timedelta
from auth_helpers import require_granular_permission
import json

restaurant_advanced_bp = Blueprint('restaurant_advanced', __name__, url_prefix='/restaurant')

# ==================== WASTE MANAGEMENT ====================

@restaurant_advanced_bp.route('/waste', methods=['GET'])
@login_required
def waste_list():
    """قائمة الفاقد والهدر"""
    if not current_user.has_granular_permission('restaurant_view_waste'):
        flash('ليس لديك صلاحية لعرض سجلات الفاقد', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    reason_filter = request.args.get('reason', '')
    
    query = FoodWaste.query
    
    if search:
        query = query.join(Item).filter(
            Item.name.ilike(f'%{search}%') |
            Item.code.ilike(f'%{search}%')
        )
    
    if reason_filter:
        query = query.filter_by(waste_reason=reason_filter)
    
    query = query.order_by(FoodWaste.waste_date.desc())
    pagination = query.paginate(page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 15))
    
    return render_template(
        'restaurant/waste_list.html',
        waste_records=pagination.items,
        pages=pagination.pages,
        current_page=page,
        search=search,
        reason_filter=reason_filter
    )


@restaurant_advanced_bp.route('/waste/add', methods=['GET', 'POST'])
@login_required
def add_waste():
    """إضافة تسجيل فاقد/هدر جديد"""
    if not current_user.has_granular_permission('restaurant_add_waste'):
        flash('ليس لديك صلاحية لإضافة سجلات الفاقد', 'danger')
        return redirect(url_for('restaurant_advanced.waste_list'))
    
    if request.method == 'POST':
        try:
            waste = FoodWaste(
                meal_record_id=request.form.get('meal_record_id') or None,
                item_id=request.form.get('item_id') or None,
                recipe_id=request.form.get('recipe_id') or None,
                waste_date=datetime.strptime(request.form.get('waste_date'), '%Y-%m-%d').date(),
                waste_reason=request.form.get('waste_reason'),
                quantity_wasted=float(request.form.get('quantity_wasted')),
                unit=request.form.get('unit'),
                estimated_unit_cost=float(request.form.get('estimated_unit_cost', 0)),
                reported_by_id=current_user.id,
                description=request.form.get('description', ''),
            )
            
            waste.calculate_waste_value()
            db.session.add(waste)
            db.session.flush()
            
            # تسجيل النشاط
            activity = ActivityLog(
                user_id=current_user.id,
                action=f"إضافة سجل فاقد: {waste.quantity_wasted} {waste.unit}",
                entity_type='FoodWaste',
                entity_id=waste.id
            )
            db.session.add(activity)
            db.session.commit()
            
            flash('تم تسجيل الفاقد بنجاح', 'success')
            return redirect(url_for('restaurant_advanced.waste_list'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
            return redirect(url_for('restaurant_advanced.add_waste'))
    
    items = Item.query.filter_by(is_active=True).all()
    recipes = Recipe.query.filter_by(is_active=True).all()
    meal_records = MealRecord.query.order_by(MealRecord.record_date.desc()).limit(50).all()
    
    return render_template(
        'restaurant/add_waste.html',
        items=items,
        recipes=recipes,
        meal_records=meal_records
    )


@restaurant_advanced_bp.route('/waste/<waste_id>/approve', methods=['POST'])
@login_required
def approve_waste(waste_id):
    """الموافقة على سجل الفاقد"""
    if not current_user.has_granular_permission('restaurant_approve_waste'):
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية'}), 403
    
    waste = FoodWaste.query.get(waste_id)
    if not waste:
        return jsonify({'success': False, 'error': 'السجل غير موجود'}), 404
    
    try:
        waste.is_approved = True
        waste.approved_by_id = current_user.id
        waste.approval_date = datetime.utcnow()
        waste.approval_notes = request.form.get('approval_notes', '')
        
        db.session.commit()
        
        flash('تمت الموافقة على الفاقد', 'success')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@restaurant_advanced_bp.route('/waste/analysis', methods=['GET'])
@login_required
def waste_analysis():
    """تحليل الفاقد والهدر"""
    if not current_user.has_granular_permission('restaurant_view_waste_reports'):
        flash('ليس لديك صلاحية لعرض التقارير', 'danger')
        return redirect(url_for('dashboard.index'))
    
    period = request.args.get('period', 'monthly')
    
    # حساب الإحصائيات
    if period == 'daily':
        date_from = date.today()
        date_to = date.today()
    elif period == 'weekly':
        today = date.today()
        date_from = today - timedelta(days=today.weekday())
        date_to = today
    else:  # monthly
        today = date.today()
        date_from = today.replace(day=1)
        date_to = today
    
    waste_records = FoodWaste.query.filter(
        FoodWaste.waste_date.between(date_from, date_to),
        FoodWaste.is_approved == True
    ).all()
    
    total_waste_quantity = sum(w.quantity_wasted for w in waste_records)
    total_waste_value = sum(w.total_waste_value for w in waste_records)
    
    # تصنيف حسب السبب
    reasons_count = {}
    for waste in waste_records:
        reasons_count[waste.waste_reason] = reasons_count.get(waste.waste_reason, 0) + 1
    
    return render_template(
        'restaurant/waste_analysis.html',
        waste_records=waste_records,
        total_quantity=total_waste_quantity,
        total_value=total_waste_value,
        reasons_count=reasons_count,
        period=period,
        date_from=date_from,
        date_to=date_to
    )


# ==================== DEMAND FORECASTING ====================

@restaurant_advanced_bp.route('/forecast', methods=['GET'])
@login_required
def forecast_list():
    """قائمة توقعات الطلب"""
    if not current_user.has_granular_permission('restaurant_view_forecast'):
        flash('ليس لديك صلاحية لعرض التوقعات', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from')
    
    query = DemandForecast.query.order_by(DemandForecast.forecast_date.desc())
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(DemandForecast.forecast_date >= date_from)
        except:
            pass
    
    pagination = query.paginate(page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 15))
    
    return render_template(
        'restaurant/forecast_list.html',
        forecasts=pagination.items,
        pages=pagination.pages,
        current_page=page,
        date_from=date_from
    )


@restaurant_advanced_bp.route('/forecast/add', methods=['GET', 'POST'])
@login_required
def add_forecast():
    """إضافة توقع طلب جديد"""
    if not current_user.has_granular_permission('restaurant_add_forecast'):
        flash('ليس لديك صلاحية لإضافة توقعات', 'danger')
        return redirect(url_for('restaurant_advanced.forecast_list'))
    
    if request.method == 'POST':
        try:
            forecast_date = datetime.strptime(request.form.get('forecast_date'), '%Y-%m-%d').date()
            
            # التحقق من عدم وجود توقع لنفس التاريخ والنوع
            existing = DemandForecast.query.filter_by(
                forecast_date=forecast_date,
                meal_type=request.form.get('meal_type')
            ).first()
            
            if existing:
                flash('توقع لهذا اليوم والنوع موجود بالفعل', 'warning')
                return redirect(url_for('restaurant_advanced.add_forecast'))
            
            forecast = DemandForecast(
                forecast_date=forecast_date,
                meal_type=request.form.get('meal_type'),
                forecasted_portions=int(request.form.get('forecasted_portions')),
                confidence_level=float(request.form.get('confidence_level', 0.8)),
                forecasting_method=request.form.get('forecasting_method', 'statistical'),
                special_event=request.form.get('special_event') == 'on',
                event_description=request.form.get('event_description', ''),
                is_holiday=request.form.get('is_holiday') == 'on',
                notes=request.form.get('notes', '')
            )
            
            db.session.add(forecast)
            db.session.commit()
            
            flash('تم إضافة التوقع بنجاح', 'success')
            return redirect(url_for('restaurant_advanced.forecast_list'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
            return redirect(url_for('restaurant_advanced.add_forecast'))
    
    return render_template('restaurant/add_forecast.html')


@restaurant_advanced_bp.route('/forecast/<forecast_id>/update-actual', methods=['POST'])
@login_required
def update_forecast_actual(forecast_id):
    """تحديث الاستهلاك الفعلي للتوقع"""
    if not current_user.has_granular_permission('restaurant_edit_forecast'):
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية'}), 403
    
    forecast = DemandForecast.query.get(forecast_id)
    if not forecast:
        return jsonify({'success': False, 'error': 'التوقع غير موجود'}), 404
    
    try:
        forecast.actual_portions = int(request.form.get('actual_portions'))
        forecast.actual_consumption = float(request.form.get('actual_consumption', 0))
        forecast.calculate_error()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'forecast_error': forecast.forecast_error,
            'error_percentage': forecast.error_percentage
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@restaurant_advanced_bp.route('/forecast/analysis', methods=['GET'])
@login_required
def forecast_analysis():
    """تحليل التوقعات والطلب"""
    if not current_user.has_granular_permission('restaurant_view_forecast_reports'):
        flash('ليس لديك صلاحية لعرض التقارير', 'danger')
        return redirect(url_for('dashboard.index'))
    
    period = request.args.get('period', 'monthly')
    
    if period == 'daily':
        date_from = date.today()
        date_to = date.today()
    elif period == 'weekly':
        today = date.today()
        date_from = today - timedelta(days=today.weekday())
        date_to = today
    else:  # monthly
        today = date.today()
        date_from = today.replace(day=1)
        date_to = today
    
    forecasts = DemandForecast.query.filter(
        DemandForecast.forecast_date.between(date_from, date_to),
        DemandForecast.actual_portions != None
    ).all()
    
    # حساب المتوسطات والدقة
    total_forecasted = sum(f.forecasted_portions for f in forecasts) if forecasts else 0
    total_actual = sum(f.actual_portions for f in forecasts) if forecasts else 0
    
    if forecasts:
        avg_error_percentage = sum(f.error_percentage or 0 for f in forecasts) / len(forecasts)
        forecast_accuracy = 100 - avg_error_percentage
    else:
        forecast_accuracy = 0
        avg_error_percentage = 0
    
    return render_template(
        'restaurant/forecast_analysis.html',
        forecasts=forecasts,
        total_forecasted=total_forecasted,
        total_actual=total_actual,
        forecast_accuracy=forecast_accuracy,
        avg_error=avg_error_percentage,
        period=period,
        date_from=date_from,
        date_to=date_to
    )


# ==================== EMPLOYEE MEAL SUBSIDY ====================

@restaurant_advanced_bp.route('/subsidy', methods=['GET'])
@login_required
def subsidy_list():
    """قائمة الدعم والخصومات"""
    if not current_user.has_granular_permission('restaurant_view_subsidy'):
        flash('ليس لديك صلاحية لعرض الدعم', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    active_only = request.args.get('active_only', 'on') == 'on'
    
    query = EmployeeMealSubsidy.query
    
    if active_only:
        query = query.filter_by(is_active=True)
    
    query = query.order_by(EmployeeMealSubsidy.start_date.desc())
    pagination = query.paginate(page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 15))
    
    return render_template(
        'restaurant/subsidy_list.html',
        subsidies=pagination.items,
        pages=pagination.pages,
        current_page=page,
        active_only=active_only
    )


@restaurant_advanced_bp.route('/subsidy/add', methods=['GET', 'POST'])
@login_required
def add_subsidy():
    """إضافة دعم/خصم للموظف"""
    if not current_user.has_granular_permission('restaurant_add_subsidy'):
        flash('ليس لديك صلاحية لإضافة الدعم', 'danger')
        return redirect(url_for('restaurant_advanced.subsidy_list'))
    
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            
            subsidy = EmployeeMealSubsidy(
                user_id=user_id,
                subsidy_type=request.form.get('subsidy_type'),
                subsidy_value=float(request.form.get('subsidy_value')),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None,
                reason=request.form.get('reason'),
                approved_by_id=current_user.id,
                notes=request.form.get('notes', '')
            )
            
            db.session.add(subsidy)
            db.session.commit()
            
            # تسجيل النشاط
            activity = ActivityLog(
                user_id=current_user.id,
                action=f"إضافة دعم للموظف",
                entity_type='EmployeeMealSubsidy',
                entity_id=subsidy.id
            )
            db.session.add(activity)
            db.session.commit()
            
            flash('تم إضافة الدعم بنجاح', 'success')
            return redirect(url_for('restaurant_advanced.subsidy_list'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
            return redirect(url_for('restaurant_advanced.add_subsidy'))
    
    users = User.query.filter_by(is_active=True).all()
    return render_template('restaurant/add_subsidy.html', users=users)


@restaurant_advanced_bp.route('/subsidy/<subsidy_id>/deactivate', methods=['POST'])
@login_required
def deactivate_subsidy(subsidy_id):
    """إلغاء نشاط الدعم"""
    if not current_user.has_granular_permission('restaurant_edit_subsidy'):
        return jsonify({'success': False, 'error': 'ليس لديك صلاحية'}), 403
    
    subsidy = EmployeeMealSubsidy.query.get(subsidy_id)
    if not subsidy:
        return jsonify({'success': False, 'error': 'الدعم غير موجود'}), 404
    
    try:
        subsidy.is_active = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@restaurant_advanced_bp.route('/payroll-summary', methods=['GET'])
@login_required
def payroll_summary():
    """ملخص الأجور والوجبات"""
    if not current_user.has_granular_permission('restaurant_view_payroll'):
        flash('ليس لديك صلاحية لعرض ملخص الأجور', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    period = request.args.get('period')
    
    query = MealPayrollIntegration.query
    
    if period:
        query = query.filter_by(payroll_period=period)
    
    query = query.order_by(MealPayrollIntegration.payroll_period.desc())
    pagination = query.paginate(page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 15))
    
    return render_template(
        'restaurant/payroll_summary.html',
        records=pagination.items,
        pages=pagination.pages,
        current_page=page,
        period=period
    )