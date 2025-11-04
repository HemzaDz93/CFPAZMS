"""
نظام إدارة وجبات الموظفين
تسجيل يومي للوجبات وحساب التكاليف (2.5 دج لكل وجبة)
وصول شهرية وتنبيهات عند التجاوز
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, current_app, jsonify
)
from flask_login import login_required, current_user
from models import (
    db, User, EmployeeMealTransaction, MealPayrollIntegration, 
    EmployeeMealAlert, ActivityLog, UserRole, MealRecord, Recipe, OrganizationSettings
)
from datetime import datetime, date, timedelta
from calendar import monthrange
from auth_helpers import require_granular_permission
from sqlalchemy import func, desc
from config import Config
from flask_sqlalchemy import SQLAlchemy

employee_meals_bp = Blueprint('employee_meals', __name__, url_prefix='/employee-meals')

# ==================== Helper Functions ====================

def get_meal_cost_per_unit():
    """الحصول على سعر الوجبة من إعدادات النظام"""
    org_settings = OrganizationSettings.query.first()
    if org_settings and org_settings.meal_cost_per_unit:
        return org_settings.meal_cost_per_unit
    return Config.MEAL_COST_PER_UNIT  # القيمة الافتراضية من الإعدادات

def get_meal_alert_threshold():
    """الحصول على عتبة التنبيه من إعدادات النظام"""
    org_settings = OrganizationSettings.query.first()
    if org_settings and org_settings.meal_alert_threshold:
        return org_settings.meal_alert_threshold
    return Config.MEAL_ALERT_THRESHOLD  # القيمة الافتراضية من الإعدادات

# ==================== Dashboard ====================

@employee_meals_bp.route('/', methods=['GET'])
@login_required
def index():
    """لوحة معلومات وجبات الموظفين"""
    if not current_user.has_granular_permission('restaurant_view_employee_meals'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # إحصائيات عامة
    total_transactions = EmployeeMealTransaction.query.count()
    total_cost = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).scalar() or 0
    unsettled_cost = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).filter_by(is_settled=False).scalar() or 0
    total_employees = User.query.count()
    
    # آخر المعاملات
    recent_transactions = EmployeeMealTransaction.query.order_by(desc(EmployeeMealTransaction.transaction_date)).limit(10).all()
    
    # التنبيهات النشطة
    active_alerts = EmployeeMealAlert.query.filter_by(is_resolved=False).count()
    
    return render_template(
        'restaurant/employee_meals/index.html',
        total_transactions=total_transactions,
        total_cost=total_cost,
        unsettled_cost=unsettled_cost,
        total_employees=total_employees,
        recent_transactions=recent_transactions,
        active_alerts=active_alerts
    )

# ==================== Daily Meal Registration ====================

@employee_meals_bp.route('/daily-registration', methods=['GET', 'POST'])
@login_required
def daily_registration():
    """تسجيل وجبات الموظفين اليومية"""
    # التحقق من الصلاحية
    if not current_user.has_granular_permission('restaurant_add_employee_meal'):
        flash('ليس لديك صلاحية للقيام بهذا الإجراء', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            meal_count = int(request.form.get('meal_count', 1))
            transaction_date_str = request.form.get('transaction_date', datetime.now().strftime('%Y-%m-%d'))
            notes = request.form.get('notes', '')
            
            # تحويل التاريخ
            if isinstance(transaction_date_str, str):
                transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()
                transaction_datetime = datetime.combine(transaction_date, datetime.min.time())
            else:
                transaction_date = transaction_date_str
                transaction_datetime = datetime.combine(transaction_date, datetime.min.time())
            
            # التحقق من المستخدم
            user = User.query.get(user_id)
            if not user:
                flash('المستخدم غير موجود', 'danger')
                return redirect(url_for('employee_meals.daily_registration'))
            
            # حساب التكلفة
            meal_cost = meal_count * get_meal_cost_per_unit()
            
            # الحصول على أو إنشاء meal_record للتاريخ المحدد
            meal_record = MealRecord.query.filter_by(
                record_date=transaction_date,
                meal_type='daily'
            ).first()
            
            if not meal_record:
                # إنشاء meal_record جديد إذا لم يكن موجوداً
                # نبحث عن أي recipe موجود أو نستخدم recipe افتراضي
                default_recipe = Recipe.query.first()
                
                if not default_recipe:
                    flash('لا توجد وصفات محددة في النظام. يرجى إضافة وصفة أولاً', 'danger')
                    return redirect(url_for('employee_meals.daily_registration'))
                
                meal_record = MealRecord(
                    record_date=transaction_date,
                    meal_type='daily',
                    recipe_id=default_recipe.id,
                    servings=meal_count,
                    expected_cost=meal_cost,
                    notes='سجل وجبات يومي تلقائي'
                )
                db.session.add(meal_record)
                db.session.flush()
            
            # إنشاء سجل المعاملة الجديد
            transaction = EmployeeMealTransaction(
                user_id=user_id,
                meal_record_id=meal_record.id,
                transaction_date=transaction_datetime,
                meal_cost=meal_cost,
                discount_percentage=0,
                discount_amount=0,
                final_cost=meal_cost,
                payment_method='deferred',
                is_settled=False,
                notes=f"{meal_count} وجبات - {notes}" if notes else f"{meal_count} وجبات"
            )
            
            db.session.add(transaction)
            db.session.flush()
            
            # التحقق من التنبيهات
            check_meal_alert(user_id, meal_cost)
            
            # تسجيل النشاط
            activity = ActivityLog(
                user_id=current_user.id,
                action=f"تسجيل {meal_count} وجبة لـ {user.full_name}",
                entity_type='EmployeeMealTransaction',
                entity_id=transaction.id
            )
            db.session.add(activity)
            
            db.session.commit()
            
            flash(f'تم تسجيل {meal_count} وجبة للموظف {user.full_name} بنجاح', 'success')
            return redirect(url_for('employee_meals.daily_registration'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ: {str(e)}', 'danger')
            return redirect(url_for('employee_meals.daily_registration'))
    
    # جلب الموظفين النشطين (عدا المديرين والعاملين)
    employees = User.query.filter_by(is_active=True).order_by(User.first_name).all()
    
    return render_template(
        'restaurant/employee_meals/daily_registration.html',
        employees=employees,
        today=date.today()
    )


@employee_meals_bp.route('/employee-meals-list', methods=['GET'])
@login_required
def meals_list():
    """عرض سجل وجبات الموظفين"""
    if not current_user.has_granular_permission('restaurant_view_employee_meals'):
        flash('ليس لديك صلاحية لعرض هذا المحتوى', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    employee_id = request.args.get('employee_id', '')
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    query = EmployeeMealTransaction.query
    
    # تصفية بالموظف
    if employee_id:
        query = query.filter_by(user_id=employee_id)
    
    # تصفية بالشهر
    if month:
        try:
            start_date = datetime.strptime(f"{month}-01", "%Y-%m-%d").date()
            end_date = date(start_date.year, start_date.month, monthrange(start_date.year, start_date.month)[1])
            query = query.filter(
                EmployeeMealTransaction.transaction_date >= datetime.combine(start_date, datetime.min.time()),
                EmployeeMealTransaction.transaction_date <= datetime.combine(end_date, datetime.max.time())
            )
        except:
            pass
    
    pagination = query.order_by(desc(EmployeeMealTransaction.transaction_date)).paginate(
        page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 20)
    )
    
    employees = User.query.filter_by(is_active=True).order_by(User.first_name).all()
    
    return render_template(
        'restaurant/employee_meals/meals_list.html',
        transactions=pagination.items,
        pages=pagination.pages,
        current_page=page,
        employees=employees,
        employee_id=employee_id,
        month=month
    )


# ==================== Monthly Receipt ====================

@employee_meals_bp.route('/monthly-receipt/<employee_id>/<month>', methods=['GET'])
@login_required
def monthly_receipt(employee_id, month):
    """عرض وطباعة الوصل الشهري للموظف"""
    if not current_user.has_granular_permission('restaurant_view_employee_receipt'):
        flash('ليس لديك صلاحية لعرض التقارير', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # جلب الموظف
    employee = User.query.get(employee_id)
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('employee_meals.meals_list'))
    
    # حساب فترة الشهر
    try:
        start_date = datetime.strptime(f"{month}-01", "%Y-%m-%d").date()
        end_date = date(start_date.year, start_date.month, monthrange(start_date.year, start_date.month)[1])
    except:
        flash('الشهر غير صحيح', 'danger')
        return redirect(url_for('employee_meals.meals_list'))
    
    # جلب جميع العمليات
    transactions = EmployeeMealTransaction.query.filter(
        EmployeeMealTransaction.user_id == employee_id,
        EmployeeMealTransaction.transaction_date >= datetime.combine(start_date, datetime.min.time()),
        EmployeeMealTransaction.transaction_date <= datetime.combine(end_date, datetime.max.time())
    ).order_by(EmployeeMealTransaction.transaction_date).all()
    
    # الحسابات
    total_meals = len(transactions)
    total_cost = sum(t.meal_cost for t in transactions)
    settled_count = len([t for t in transactions if t.is_settled])
    unsettled_count = total_meals - settled_count
    unsettled_cost = unsettled_count * get_meal_cost_per_unit()
    
    # جلب أو إنشاء سجل الراتب
    payroll_record = MealPayrollIntegration.query.filter_by(
        user_id=employee_id,
        payroll_period=month
    ).first()
    
    if not payroll_record:
        payroll_record = MealPayrollIntegration(
            user_id=employee_id,
            payroll_period=month
        )
        payroll_record.calculate_totals()
    
    return render_template(
        'restaurant/employee_meals/monthly_receipt.html',
        employee=employee,
        month=month,
        start_date=start_date,
        end_date=end_date,
        transactions=transactions,
        total_meals=total_meals,
        total_cost=total_cost,
        settled_count=settled_count,
        unsettled_count=unsettled_count,
        unsettled_cost=unsettled_cost,
        payroll_record=payroll_record,
        meal_cost_unit=get_meal_cost_per_unit()
    )


@employee_meals_bp.route('/mark-settled/<transaction_id>', methods=['POST'])
@login_required
def mark_settled(transaction_id):
    """تحديد عملية كمدفوعة"""
    if not current_user.has_granular_permission('restaurant_edit_employee_meal'):
        flash('ليس لديك صلاحية', 'danger')
        return jsonify({'success': False}), 403
    
    transaction = EmployeeMealTransaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'success': False, 'message': 'العملية غير موجودة'}), 404
    
    try:
        transaction.is_settled = True
        transaction.settlement_date = datetime.utcnow()
        transaction.settlement_notes = request.form.get('notes', '')
        db.session.commit()
        
        # تحديث التنبيهات
        check_meal_alert(transaction.user_id, -transaction.final_cost)
        
        return jsonify({'success': True, 'message': 'تم تحديث الحالة'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== Alerts ====================

@employee_meals_bp.route('/alerts', methods=['GET'])
@login_required
def alerts_list():
    """عرض قائمة التنبيهات"""
    if not current_user.has_granular_permission('restaurant_view_employee_alerts'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    show_resolved = request.args.get('show_resolved', 'false').lower() == 'true'
    
    query = EmployeeMealAlert.query
    
    if not show_resolved:
        query = query.filter_by(is_resolved=False)
    
    pagination = query.order_by(desc(EmployeeMealAlert.alert_date)).paginate(
        page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 20)
    )
    
    return render_template(
        'restaurant/employee_meals/alerts_list.html',
        alerts=pagination.items,
        pages=pagination.pages,
        current_page=page,
        show_resolved=show_resolved
    )


@employee_meals_bp.route('/alert/<alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """تحديد التنبيه كمحل"""
    if not current_user.has_granular_permission('restaurant_view_employee_alerts'):
        return jsonify({'success': False}), 403
    
    alert = EmployeeMealAlert.query.get(alert_id)
    if not alert:
        return jsonify({'success': False, 'message': 'التنبيه غير موجود'}), 404
    
    try:
        alert.is_resolved = True
        alert.resolved_date = datetime.utcnow()
        alert.resolved_by = current_user.id
        alert.notes = request.form.get('notes', '')
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم حل التنبيه'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== Reports ====================

@employee_meals_bp.route('/monthly-report', methods=['GET'])
@login_required
def monthly_report():
    """تقرير شهري شامل لوجبات الموظفين"""
    if not current_user.has_granular_permission('restaurant_view_employee_receipt'):
        flash('ليس لديك صلاحية لعرض التقارير', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # الحصول على الشهر من الطلب
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    try:
        start_date = datetime.strptime(f"{month}-01", "%Y-%m-%d").date()
        end_date = date(start_date.year, start_date.month, monthrange(start_date.year, start_date.month)[1])
    except:
        flash('الشهر غير صحيح', 'danger')
        return redirect(url_for('employee_meals.meals_list'))
    
    # جلب جميع المعاملات للشهر المحدد
    transactions = EmployeeMealTransaction.query.filter(
        EmployeeMealTransaction.transaction_date >= datetime.combine(start_date, datetime.min.time()),
        EmployeeMealTransaction.transaction_date <= datetime.combine(end_date, datetime.max.time())
    ).order_by(EmployeeMealTransaction.transaction_date).all()
    
    # تجميع البيانات حسب الموظف
    employee_stats = {}
    for trans in transactions:
        emp_id = trans.user_id
        if emp_id not in employee_stats:
            employee_stats[emp_id] = {
                'employee': trans.user,
                'transactions': [],
                'total_meals': 0,
                'total_cost': 0,
                'settled_count': 0,
                'settled_cost': 0
            }
        
        employee_stats[emp_id]['transactions'].append(trans)
        employee_stats[emp_id]['total_meals'] += int(trans.meal_cost / get_meal_cost_per_unit())
        employee_stats[emp_id]['total_cost'] += trans.final_cost
        
        if trans.is_settled:
            employee_stats[emp_id]['settled_count'] += int(trans.meal_cost / get_meal_cost_per_unit())
            employee_stats[emp_id]['settled_cost'] += trans.final_cost
    
    # حساب الإجماليات
    grand_total_meals = sum(s['total_meals'] for s in employee_stats.values())
    grand_total_cost = sum(s['total_cost'] for s in employee_stats.values())
    grand_settled_count = sum(s['settled_count'] for s in employee_stats.values())
    grand_settled_cost = sum(s['settled_cost'] for s in employee_stats.values())
    grand_unsettled_cost = grand_total_cost - grand_settled_cost
    
    # ترتيب حسب أسماء الموظفين
    sorted_stats = sorted(employee_stats.items(), key=lambda x: x[1]['employee'].full_name)
    
    return render_template(
        'restaurant/employee_meals/monthly_report.html',
        month=month,
        start_date=start_date,
        end_date=end_date,
        employee_stats=sorted_stats,
        grand_total_meals=grand_total_meals,
        grand_total_cost=grand_total_cost,
        grand_settled_count=grand_settled_count,
        grand_settled_cost=grand_settled_cost,
        grand_unsettled_cost=grand_unsettled_cost,
        transactions_count=len(transactions),
        meal_cost_unit=get_meal_cost_per_unit()
    )


@employee_meals_bp.route('/employee-summary/<employee_id>', methods=['GET'])
@login_required
def employee_summary(employee_id):
    """ملخص استهلاك الموظف للوجبات"""
    if not current_user.has_granular_permission('restaurant_view_employee_receipt'):
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('dashboard.index'))
    
    employee = User.query.get(employee_id)
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('employee_meals.meals_list'))
    
    # الإحصائيات
    total_transactions = EmployeeMealTransaction.query.filter_by(user_id=employee_id).count()
    total_cost = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).filter_by(user_id=employee_id).scalar() or 0
    settled_cost = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).filter_by(user_id=employee_id, is_settled=True).scalar() or 0
    unsettled_cost = total_cost - settled_cost
    
    # السجلات الشهرية
    payroll_records = MealPayrollIntegration.query.filter_by(user_id=employee_id).order_by(desc(MealPayrollIntegration.payroll_period)).all()
    
    # التنبيهات
    alerts = EmployeeMealAlert.query.filter_by(user_id=employee_id, is_resolved=False).all()
    
    return render_template(
        'restaurant/employee_meals/employee_summary.html',
        employee=employee,
        total_transactions=total_transactions,
        total_cost=total_cost,
        settled_cost=settled_cost,
        unsettled_cost=unsettled_cost,
        payroll_records=payroll_records,
        alerts=alerts,
        meal_cost_unit=get_meal_cost_per_unit()
    )


# ==================== Payment Management ====================

@employee_meals_bp.route('/payments', methods=['GET'])
@login_required
def payments_list():
    """عرض قائمة الدفعات وإدارة الدفع"""
    if not current_user.has_granular_permission('restaurant_view_employee_payments'):
        flash('ليس لديك صلاحية لإدارة الدفعات', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    employee_id = request.args.get('employee_id', '')
    status_filter = request.args.get('status', 'unsettled')  # unsettled, settled, all
    
    query = EmployeeMealTransaction.query
    stats_query = EmployeeMealTransaction.query  # Separate query for statistics
    
    # تصفية بالموظف
    if employee_id:
        query = query.filter_by(user_id=employee_id)
        stats_query = stats_query.filter_by(user_id=employee_id)
    
    # تصفية بالحالة
    if status_filter == 'unsettled':
        query = query.filter_by(is_settled=False)
        stats_query = stats_query.filter_by(is_settled=False)
    elif status_filter == 'settled':
        query = query.filter_by(is_settled=True)
        stats_query = stats_query.filter_by(is_settled=True)
    
    pagination = query.order_by(desc(EmployeeMealTransaction.transaction_date)).paginate(
        page=page, per_page=current_app.config.get('ITEMS_PER_PAGE', 20)
    )
    
    # إحصائيات الدفع (تطبيق نفس الفلاتر)
    unsettled_total = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).filter_by(is_settled=False)
    settled_total = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).filter_by(is_settled=True)
    
    # تطبيق فلتر الموظف على الإحصائيات العامة إذا لزم الأمر
    if not employee_id:
        # إذا لم يتم تحديد موظف، عرض الإحصائيات العامة لجميع الموظفين
        unsettled_total = unsettled_total.scalar() or 0
        settled_total = settled_total.scalar() or 0
    else:
        # إذا تم تحديد موظف، عرض إحصائياته فقط
        unsettled_total = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).filter_by(user_id=employee_id, is_settled=False).scalar() or 0
        settled_total = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).filter_by(user_id=employee_id, is_settled=True).scalar() or 0
    
    employees = User.query.filter_by(is_active=True).order_by(User.first_name).all()
    
    # Debug logging
    current_app.logger.debug(f"Payments List - employee_id: {employee_id}, status: {status_filter}")
    current_app.logger.debug(f"Transactions count: {len(pagination.items)}, unsettled: {unsettled_total}, settled: {settled_total}")
    
    return render_template(
        'restaurant/employee_meals/payments_list.html',
        transactions=pagination.items,
        pages=pagination.pages,
        current_page=page,
        employees=employees,
        employee_id=employee_id,
        status_filter=status_filter,
        unsettled_total=unsettled_total,
        settled_total=settled_total
    )


@employee_meals_bp.route('/payment/settle/<transaction_id>', methods=['POST'])
@login_required
def settle_payment(transaction_id):
    """تسديد دفعة واحدة"""
    if not current_user.has_granular_permission('restaurant_process_employee_payment'):
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    transaction = EmployeeMealTransaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'success': False, 'message': 'العملية غير موجودة'}), 404
    
    try:
        transaction.is_settled = True
        transaction.settlement_date = datetime.utcnow()
        transaction.settlement_notes = request.form.get('notes', '')
        db.session.commit()
        
        # تحديث التنبيهات
        check_meal_alert(transaction.user_id, -transaction.final_cost)
        
        # تسجيل النشاط
        activity = ActivityLog(
            user_id=current_user.id,
            action=f"تسديد دفعة وجبات بقيمة {transaction.final_cost} دج للموظف {transaction.user.full_name}",
            entity_type='EmployeeMealTransaction',
            entity_id=transaction.id
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'تم تسديد الدفعة بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@employee_meals_bp.route('/payment/settle-employee/<employee_id>', methods=['POST'])
@login_required
def settle_employee_payments(employee_id):
    """تسديد جميع الدفعات المعلقة لموظف واحد"""
    if not current_user.has_granular_permission('restaurant_process_employee_payment'):
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    employee = User.query.get(employee_id)
    if not employee:
        return jsonify({'success': False, 'message': 'الموظف غير موجود'}), 404
    
    try:
        # جلب جميع الدفعات المعلقة
        unsettled_transactions = EmployeeMealTransaction.query.filter_by(
            user_id=employee_id,
            is_settled=False
        ).all()
        
        if not unsettled_transactions:
            return jsonify({'success': False, 'message': 'لا توجد دفعات معلقة لهذا الموظف'}), 400
        
        total_amount = 0
        for transaction in unsettled_transactions:
            transaction.is_settled = True
            transaction.settlement_date = datetime.utcnow()
            transaction.settlement_notes = request.form.get('notes', 'دفع جماعي')
            total_amount += transaction.final_cost
        
        db.session.commit()
        
        # تحديث التنبيهات
        check_meal_alert(employee_id, -total_amount)
        
        # تسجيل النشاط
        activity = ActivityLog(
            user_id=current_user.id,
            action=f"تسديد جميع دفعات الوجبات ({len(unsettled_transactions)} دفعة) للموظف {employee.full_name} بقيمة إجمالية {total_amount} دج",
            entity_type='User',
            entity_id=employee_id
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم تسديد {len(unsettled_transactions)} دفعات بنجاح، الإجمالي: {total_amount:.2f} دج'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@employee_meals_bp.route('/payment/settle-all', methods=['POST'])
@login_required
def settle_all_payments():
    """تسديد جميع الدفعات المعلقة للجميع"""
    if not current_user.has_granular_permission('restaurant_process_employee_payment'):
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    try:
        # جلب جميع الدفعات المعلقة
        unsettled_transactions = EmployeeMealTransaction.query.filter_by(
            is_settled=False
        ).all()
        
        if not unsettled_transactions:
            return jsonify({'success': False, 'message': 'لا توجد دفعات معلقة'}), 400
        
        total_amount = 0
        employees_count = set()
        
        for transaction in unsettled_transactions:
            transaction.is_settled = True
            transaction.settlement_date = datetime.utcnow()
            transaction.settlement_notes = 'دفع جماعي شامل'
            total_amount += transaction.final_cost
            employees_count.add(transaction.user_id)
        
        db.session.commit()
        
        # تسجيل النشاط
        activity = ActivityLog(
            user_id=current_user.id,
            action=f"تسديد جميع دفعات الوجبات المعلقة ({len(unsettled_transactions)} دفعة من {len(employees_count)} موظفين) بقيمة إجمالية {total_amount} دج",
            entity_type='EmployeeMealTransaction',
            entity_id='batch'
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم تسديد {len(unsettled_transactions)} دفعة من {len(employees_count)} موظف بنجاح، الإجمالي: {total_amount:.2f} دج'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== Helper Functions ====================

def check_meal_alert(user_id, amount_added):
    """فحص وإنشاء التنبيهات عند تجاوز الحد"""
    # حساب المجموع الحالي
    current_total = db.session.query(func.sum(EmployeeMealTransaction.final_cost)).filter_by(
        user_id=user_id,
        is_settled=False
    ).scalar() or 0
    
    current_total += amount_added
    
    # الحصول على عتبة التنبيه
    alert_threshold = get_meal_alert_threshold()
    
    # التحقق من التجاوز
    if current_total > alert_threshold:
        # البحث عن تنبيه موجود
        existing_alert = EmployeeMealAlert.query.filter_by(
            user_id=user_id,
            alert_type='threshold_exceeded',
            is_resolved=False
        ).first()
        
        if not existing_alert:
            # إنشاء تنبيه جديد
            alert = EmployeeMealAlert(
                user_id=user_id,
                alert_type='threshold_exceeded',
                alert_threshold=alert_threshold,
                current_amount=current_total
            )
            db.session.add(alert)
        else:
            # تحديث التنبيه الموجود
            existing_alert.current_amount = current_total
            existing_alert.alert_date = datetime.utcnow()
        
        db.session.commit()