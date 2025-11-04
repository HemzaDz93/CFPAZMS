from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, current_app
)
from flask_login import login_required, current_user
from models import (
    db, AssetRegistration, ItemIssue, Item, User, 
    ActivityLog, ItemStatus
)
from datetime import datetime
import uuid
from auth_helpers import require_granular_permission

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')

@equipment_bp.route('/', methods=['GET'])
@login_required
def index():
    """لوحة معلومات المعدات والأصول"""
    if not current_user.has_granular_permission('equipment_view_assets'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # إعادة توجيه إلى قائمة الأصول
    return redirect(url_for('equipment.assets'))

@equipment_bp.route('/assets')
@login_required
def assets():
    """قائمة الأصول/المعدات"""
    # التحقق من صلاحية عرض الأصول
    if not current_user.has_granular_permission('equipment_view_assets'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = AssetRegistration.query
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(
            (AssetRegistration.asset_code.ilike(f'%{search}%')) |
            (AssetRegistration.serial_number.ilike(f'%{search}%'))
        )
    
    assets = query.paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    can_add = current_user.has_granular_permission('equipment_add_asset')
    can_edit = current_user.has_granular_permission('equipment_edit_asset')
    can_delete = current_user.has_granular_permission('equipment_delete_asset')
    
    return render_template(
        'equipment/assets.html',
        assets=assets,
        selected_status=status,
        search=search,
        can_add=can_add,
        can_edit=can_edit,
        can_delete=can_delete
    )

@equipment_bp.route('/assets/add', methods=['GET', 'POST'])
@login_required
def add_asset():
    """إضافة أصل جديد"""
    # التحقق من صلاحية الإضافة
    if not current_user.has_granular_permission('equipment_add_asset'):
        flash('ليس لديك صلاحية لإضافة أصول', 'danger')
        return redirect(url_for('equipment.assets'))
    
    if request.method == 'POST':
        asset_code = request.form.get('asset_code', '').strip()
        item_id = request.form.get('item_id', '')
        
        if not asset_code or not item_id:
            flash('جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('equipment.add_asset'))
        
        if AssetRegistration.query.filter_by(asset_code=asset_code).first():
            flash('هذا الكود موجود بالفعل', 'danger')
            return redirect(url_for('equipment.add_asset'))
        
        asset = AssetRegistration(
            asset_code=asset_code,
            serial_number=request.form.get('serial_number', ''),
            item_id=item_id,
            acquisition_date=datetime.strptime(
                request.form.get('acquisition_date'), '%Y-%m-%d'
            ),
            acquisition_price=float(request.form.get('acquisition_price', 0)) or None,
            location=request.form.get('location', ''),
        )
        
        db.session.add(asset)
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"إضافة أصل جديد: {asset_code}",
            entity_type='AssetRegistration',
            entity_id=asset.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم إضافة الأصل بنجاح', 'success')
        return redirect(url_for('equipment.assets'))
    
    items = Item.query.filter_by(is_active=True).all()
    return render_template('equipment/add_asset.html', items=items)

@equipment_bp.route('/assets/<asset_id>')
@login_required
def view_asset(asset_id):
    """عرض تفاصيل أصل"""
    # التحقق من صلاحية العرض
    if not current_user.has_granular_permission('equipment_view_assets'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    asset = AssetRegistration.query.get_or_404(asset_id)
    can_edit = current_user.has_granular_permission('equipment_edit_asset')
    can_delete = current_user.has_granular_permission('equipment_delete_asset')
    
    return render_template('equipment/view_asset.html', asset=asset, 
                          can_edit=can_edit, can_delete=can_delete)

@equipment_bp.route('/assets/edit/<asset_id>', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):
    """تعديل أصل"""
    # التحقق من صلاحية التعديل
    if not current_user.has_granular_permission('equipment_edit_asset'):
        flash('ليس لديك صلاحية لتعديل الأصول', 'danger')
        return redirect(url_for('equipment.assets'))
    
    asset = AssetRegistration.query.get_or_404(asset_id)
    
    if request.method == 'POST':
        asset.serial_number = request.form.get('serial_number', asset.serial_number)
        asset.location = request.form.get('location', asset.location)
        asset.status = request.form.get('status', asset.status)
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"تعديل أصل: {asset.asset_code}",
            entity_type='AssetRegistration',
            entity_id=asset.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تحديث الأصل بنجاح', 'success')
        return redirect(url_for('equipment.assets'))
    
    items = Item.query.filter_by(is_active=True).all()
    return render_template('equipment/edit_asset.html', asset=asset, items=items)

@equipment_bp.route('/assets/<asset_id>/delete', methods=['POST', 'GET'])
@login_required
def delete_asset(asset_id):
    """حذف أصل"""
    # التحقق من صلاحية الحذف
    if not current_user.has_granular_permission('equipment_delete_asset'):
        flash('ليس لديك صلاحية لحذف الأصول', 'danger')
        return redirect(url_for('equipment.assets'))
    
    asset = AssetRegistration.query.get_or_404(asset_id)
    
    # Log the deletion
    activity_log = ActivityLog(
        user_id=current_user.id,
        action=f"حذف أصل: {asset.asset_code}",
        entity_type='AssetRegistration',
        entity_id=asset.id
    )
    db.session.add(activity_log)
    
    db.session.delete(asset)
    db.session.commit()
    
    flash('تم حذف الأصل بنجاح', 'success')
    return redirect(url_for('equipment.assets'))

# ==================== Item Issues (Assignments) ====================

@equipment_bp.route('/issues')
@login_required
def issues():
    """قائمة تسليمات العتاد"""
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', '')
    
    query = ItemIssue.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    issues = query.order_by(ItemIssue.issue_date.desc()).paginate(
        page=page, per_page=current_app.config['ITEMS_PER_PAGE']
    )
    
    users = User.query.all()
    return render_template(
        'equipment/issues.html',
        issues=issues,
        users=users,
        selected_user=user_id
    )

@equipment_bp.route('/issues/add', methods=['GET', 'POST'])
@login_required
def add_issue():
    """إضافة تسليم عتاد"""
    if request.method == 'POST':
        user_id = request.form.get('user_id', '')
        asset_id = request.form.get('asset_id', '')
        
        if not user_id or not asset_id:
            flash('جميع الحقول مطلوبة', 'warning')
            return redirect(url_for('equipment.add_issue'))
        
        user = User.query.get_or_404(user_id)
        asset = AssetRegistration.query.get_or_404(asset_id)
        
        # التحقق من عدم وجود تسليم نشط للأصل
        active_issue = ItemIssue.query.filter_by(
            asset_id=asset_id,
            actual_return_date=None
        ).first()
        
        if active_issue:
            flash('هذا الأصل مسلم بالفعل لموظف آخر', 'danger')
            return redirect(url_for('equipment.add_issue'))
        
        # معالجة تاريخ الإرجاع المتوقع
        expected_return_date = request.form.get('expected_return_date')
        if expected_return_date:
            expected_return_date = datetime.strptime(expected_return_date, '%Y-%m-%d').date()
        else:
            expected_return_date = None
        
        issue = ItemIssue(
            issue_number=f"ISS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6].upper()}",
            user_id=user_id,
            asset_id=asset_id,
            expected_return_date=expected_return_date,
            condition_on_issue=request.form.get('condition_on_issue', ''),
            notes=request.form.get('notes', ''),
        )
        
        asset.status = 'in_service'
        
        db.session.add(issue)
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"تسليم عتاد: {asset.asset_code} للموظف {user.full_name}",
            entity_type='ItemIssue',
            entity_id=issue.id
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تسجيل التسليم بنجاح', 'success')
        return redirect(url_for('equipment.issues'))
    
    users = User.query.all()
    assets = AssetRegistration.query.filter_by(status='in_service').all()
    
    # الأصول غير المسلمة
    unassigned_assets = AssetRegistration.query.filter(
        ~AssetRegistration.assignments.any(
            ItemIssue.actual_return_date == None
        )
    ).all()
    
    return render_template(
        'equipment/add_issue.html',
        users=users,
        assets=unassigned_assets
    )

@equipment_bp.route('/issues/return/<issue_id>', methods=['GET', 'POST'])
@login_required
def return_issue(issue_id):
    """إرجاع عتاد"""
    issue = ItemIssue.query.get_or_404(issue_id)
    
    if issue.actual_return_date:
        flash('هذا العتاد مسترجع بالفعل', 'info')
        return redirect(url_for('equipment.issues'))
    
    if request.method == 'POST':
        issue.actual_return_date = datetime.utcnow()
        issue.condition_on_return = request.form.get('condition_on_return', '')
        issue.notes = request.form.get('notes', issue.notes)
        
        # تحديث حالة الأصل
        if 'damaged' in request.form:
            issue.asset.status = 'defective'
        elif 'lost' in request.form:
            issue.asset.status = 'lost'
        else:
            issue.asset.status = 'returned'
        
        db.session.commit()
        
        activity_log = ActivityLog(
            user_id=current_user.id,
            action=f"إرجاع عتاد: {issue.asset.asset_code} من {issue.issued_to.full_name}",
            entity_type='ItemIssue',
            entity_id=issue.id,
            new_value=f"الحالة: {issue.asset.status}"
        )
        db.session.add(activity_log)
        db.session.commit()
        
        flash('تم تسجيل الإرجاع بنجاح', 'success')
        return redirect(url_for('equipment.issues'))
    
    return render_template('equipment/return_issue.html', issue=issue)