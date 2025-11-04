from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Notification
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/', methods=['GET'])
@login_required
def list_notifications():
    """عرض قائمة الإشعارات"""
    if not current_user.has_granular_permission('notifications_view'):
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # الحصول على معاملات الترقيم
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    filter_type = request.args.get('filter', 'all', type=str)  # all, unread, read
    
    # بناء الاستعلام
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # تطبيق الفلتر
    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_type == 'read':
        query = query.filter_by(is_read=True)
    
    # ترتيب حسب الأحدث أولاً
    query = query.order_by(Notification.created_at.desc())
    
    # الحصول على الإشعارات المصفاة
    paginated_notifications = query.paginate(page=page, per_page=per_page)
    
    # إحصائيات الإشعارات
    total_count = Notification.query.filter_by(user_id=current_user.id).count()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    read_count = Notification.query.filter_by(user_id=current_user.id, is_read=True).count()
    
    return render_template('notifications/list.html',
                         notifications=paginated_notifications,
                         filter_type=filter_type,
                         stats={
                             'total': total_count,
                             'unread': unread_count,
                             'read': read_count
                         })


@notifications_bp.route('/<notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """تحديد إشعار كمقروء"""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    
    if not notification:
        return jsonify({'success': False, 'message': 'الإشعار غير موجود'}), 404
    
    notification.mark_as_read()
    
    return jsonify({
        'success': True,
        'message': 'تم تحديد الإشعار كمقروء',
        'is_read': notification.is_read
    })


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """تحديد جميع الإشعارات كمقروءة"""
    if not current_user.has_granular_permission('notifications_manage'):
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in unread_notifications:
        notification.mark_as_read()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'تم تحديد {len(unread_notifications)} إشعار كمقروء',
        'count': len(unread_notifications)
    })


@notifications_bp.route('/<notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """حذف إشعار"""
    if not current_user.has_granular_permission('notifications_manage'):
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    
    if not notification:
        return jsonify({'success': False, 'message': 'الإشعار غير موجود'}), 404
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'تم حذف الإشعار بنجاح'
    })


@notifications_bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    """حذف جميع الإشعارات"""
    if not current_user.has_granular_permission('notifications_manage'):
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    all_notifications = Notification.query.filter_by(user_id=current_user.id).all()
    count = len(all_notifications)
    
    for notification in all_notifications:
        db.session.delete(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'تم حذف {count} إشعار',
        'count': count
    })


@notifications_bp.route('/api/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """الحصول على عدد الإشعارات غير المقروءة"""
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({
        'success': True,
        'unread_count': unread_count
    })