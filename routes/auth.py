from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from models import db, User, UserRole, VocationalCenter
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        center_id = request.form.get('center_id', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # التحقق من اختيار المؤسسة
        if not center_id:
            flash('يرجى اختيار المؤسسة التكوينية', 'warning')
            centers = VocationalCenter.query.filter_by(is_active=True).all()
            return render_template('auth/login.html', centers=centers)
        
        # التحقق من وجود المؤسسة
        center = VocationalCenter.query.filter_by(id=center_id, is_active=True).first()
        if not center:
            flash('المؤسسة المختارة غير موجودة أو معطلة', 'danger')
            centers = VocationalCenter.query.filter_by(is_active=True).all()
            return render_template('auth/login.html', centers=centers)
        
        if not username or not password:
            flash('يرجى إدخال اسم المستخدم وكلمة المرور', 'warning')
            centers = VocationalCenter.query.filter_by(is_active=True).all()
            return render_template('auth/login.html', centers=centers)
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('اسم المستخدم أو كلمة المرور غير صحيح', 'danger')
            centers = VocationalCenter.query.filter_by(is_active=True).all()
            return render_template('auth/login.html', centers=centers)
        
        if not user.is_active:
            flash('حسابك معطل. يرجى التواصل مع المسؤول', 'danger')
            centers = VocationalCenter.query.filter_by(is_active=True).all()
            return render_template('auth/login.html', centers=centers)
        
        # التحقق من أن المستخدم ينتمي للمؤسسة المختارة أو أنه مسؤول نظام
        if user.center_id and user.center_id != center_id and user.role != UserRole.ADMIN:
            flash('ليس لديك صلاحية للدخول من هذه المؤسسة', 'danger')
            centers = VocationalCenter.query.filter_by(is_active=True).all()
            return render_template('auth/login.html', centers=centers)
        
        # تحديث المؤسسة المختارة للمستخدم إذا كانت مختلفة
        # أو تخزينها في الجلسة للمسؤولين
        session['selected_center_id'] = center_id
        session['selected_center_name'] = center.name_ar
        
        # إذا كان المستخدم مسؤول نظام ولم يكن له مؤسسة محددة
        if user.role == UserRole.ADMIN and not user.center_id:
            user.center_id = center_id
        
        # تحديث آخر دخول
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=request.form.get('remember') is not None)
        flash(f'مرحباً {user.full_name} - {center.name_ar}', 'success')
        
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    
    # جلب قائمة المؤسسات النشطة
    centers = VocationalCenter.query.filter_by(is_active=True).all()
    return render_template('auth/login.html', centers=centers)

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل خروجك بنجاح', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """الملف الشخصي"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.email = request.form.get('email', current_user.email)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.address = request.form.get('address', current_user.address)
        
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if old_password:
            if not current_user.check_password(old_password):
                flash('كلمة المرور القديمة غير صحيحة', 'danger')
                return redirect(url_for('auth.profile'))
            
            if new_password != confirm_password:
                flash('كلمات المرور الجديدة غير متطابقة', 'warning')
                return redirect(url_for('auth.profile'))
            
            if len(new_password) < 6:
                flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'warning')
                return redirect(url_for('auth.profile'))
            
            current_user.set_password(new_password)
            flash('تم تحديث كلمة المرور بنجاح', 'success')
        
        db.session.commit()
        flash('تم تحديث الملف الشخصي بنجاح', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/user_profile.html', user=current_user)