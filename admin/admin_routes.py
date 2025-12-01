from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user, login_user, logout_user
from shared.models import db, User, Device, SensorData
from shared.forms import CreateAdminForm, LoginForm
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

# ==================== AUTENTICACIÓN ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active and user.role == 'admin':
            login_user(user, remember=True, force=True)
            flash('¡Inicio de sesión exitoso como Administrador!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Credenciales incorrectas o no tiene permisos de administrador', 'danger')
    
    return render_template('admin/login.html', form=form)

@admin_bp.route('/logout')
def admin_logout():
    logout_user()
    flash('Has cerrado sesión de administrador', 'info')
    return redirect(url_for('admin.admin_login'))

@admin_bp.before_request
def restrict_to_admin():
    # Excluir las rutas de login y logout de la restricción
    if request.endpoint in ['admin.admin_login', 'admin.admin_logout']:
        return
    
    # ✅ IMPORTANTE: También excluir la API de sensor data (para ESP32)
    if request.endpoint == 'admin.receive_sensor_data':
        return
    
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Acceso denegado. Se requiere rol de administrador.', 'danger')
        return redirect(url_for('admin.admin_login'))

# ==================== DASHBOARD ====================

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    if current_user.is_root_admin():
        total_users = User.query.filter_by(role='user', is_active=True, is_deleted=False).count()
        recent_users = User.query.filter_by(role='user', is_active=True, is_deleted=False).order_by(User.created_at.desc()).limit(5).all()
        total_admins = User.query.filter_by(role='admin', is_active=True, is_deleted=False).count() - 1
        inactive_users = User.query.filter_by(is_active=False, is_deleted=True).count()
    else:
        total_users = User.query.filter_by(role='user', is_active=True, is_deleted=False).count()
        recent_users = User.query.filter_by(role='user', is_active=True, is_deleted=False).order_by(User.created_at.desc()).limit(5).all()
        total_admins = 0
        inactive_users = User.query.filter_by(is_active=False, is_deleted=True, created_by=current_user.id).count()
    
    stats = {
        'total_users': total_users,
        'total_devices': Device.query.count(),
        'used_devices': Device.query.filter_by(is_used=True).count(),
        'available_devices': Device.query.filter_by(is_used=False).count(),
        'total_alerts': SensorData.query.filter_by(is_alert=True).count(),
        'total_admins': total_admins,
        'my_users': User.query.filter_by(created_by=current_user.id, is_active=True, is_deleted=False).count(),
        'inactive_users': inactive_users,
        'is_root_admin': current_user.is_root_admin()
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users)

# ==================== GESTIÓN DE USUARIOS ====================

@admin_bp.route('/users')
@login_required
def admin_users():
    if current_user.is_root_admin():
        users_list = User.query.filter_by(role='user', is_active=True, is_deleted=False).order_by(User.created_at.desc()).all()
    else:
        users_list = User.query.filter_by(role='user', is_active=True, is_deleted=False).order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/inactive-users')
@login_required
def admin_inactive_users():
    if current_user.is_root_admin():
        inactive_users = User.query.filter_by(is_active=False, is_deleted=True).order_by(User.deleted_at.desc()).all()
    else:
        inactive_users = User.query.filter_by(is_active=False, is_deleted=True, created_by=current_user.id).order_by(User.deleted_at.desc()).all()
    
    return render_template('admin/inactive_users.html', users=inactive_users)

@admin_bp.route('/user/deactivate/<int:user_id>', methods=['POST'])
@login_required
def admin_deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if not current_user.can_deactivate_user(user):
        flash('No tienes permisos para desactivar este usuario', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    user.deactivate_account()
    db.session.commit()
    
    flash('Usuario desactivado correctamente. El dispositivo ha sido liberado.', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/user/reactivate/<int:user_id>', methods=['POST'])
@login_required
def admin_reactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if not current_user.can_deactivate_user(user):
        flash('No tienes permisos para reactivar este usuario', 'danger')
        return redirect(url_for('admin.admin_inactive_users'))
    
    if user.device_code:
        device = Device.query.filter_by(device_code=user.device_code).first()
        if device and device.is_used:
            flash('No se puede reactivar: el dispositivo está en uso por otro usuario', 'danger')
            return redirect(url_for('admin.admin_inactive_users'))
    
    user.reactivate_account()
    db.session.commit()
    
    flash('Usuario reactivado correctamente', 'success')
    return redirect(url_for('admin.admin_inactive_users'))

@admin_bp.route('/user/delete-permanent/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_permanent(user_id):
    if not current_user.is_root_admin():
        flash('Solo el administrador principal puede eliminar usuarios permanentemente', 'danger')
        return redirect(url_for('admin.admin_inactive_users'))
    
    user = User.query.get_or_404(user_id)
    
    if not user.is_deleted:
        flash('Solo se pueden eliminar permanentemente usuarios desactivados', 'danger')
        return redirect(url_for('admin.admin_inactive_users'))
    
    if user.device_code:
        device = Device.query.filter_by(device_code=user.device_code).first()
        if device:
            device.is_used = False
    
    SensorData.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuario eliminado permanentemente del sistema', 'warning')
    return redirect(url_for('admin.admin_inactive_users'))

# ==================== GESTIÓN DE DISPOSITIVOS ====================

@admin_bp.route('/devices')
@login_required
def admin_devices():
    devices_list = Device.query.order_by(Device.created_at).all()
    return render_template('admin/devices.html', devices=devices_list)

# ==================== GESTIÓN DE ADMINISTRADORES (ROOT ONLY) ====================

@admin_bp.route('/create-admin', methods=['GET', 'POST'])
@login_required
def admin_create_admin():
    if not current_user.is_root_admin():
        flash('Solo el administrador principal puede crear nuevos administradores', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    form = CreateAdminForm()
    
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('El nombre de usuario ya existe', 'danger')
            return render_template('admin/create_admin.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado', 'danger')
            return render_template('admin/create_admin.html', form=form)
        
        admin = User(
            username=form.username.data,
            email=form.email.data,
            role='admin',
            created_by=current_user.id
        )
        admin.set_password(form.password.data)
        
        db.session.add(admin)
        db.session.commit()
        
        flash('Administrador creado exitosamente', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    
    return render_template('admin/create_admin.html', form=form)

@admin_bp.route('/admins')
@login_required
def admin_admins():
    if not current_user.is_root_admin():
        flash('Solo el administrador principal puede gestionar otros administradores', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    admins_list = User.query.filter(
        User.role == 'admin',
        User.id != current_user.id
    ).order_by(User.created_at.desc()).all()
    
    return render_template('admin/admins.html', admins=admins_list)

@admin_bp.route('/admin/delete/<int:admin_id>', methods=['POST'])
@login_required
def admin_delete_admin(admin_id):
    if not current_user.is_root_admin():
        flash('Solo el administrador principal puede eliminar otros administradores', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    target_admin = User.query.get_or_404(admin_id)
    
    if target_admin.is_root_admin():
        flash('No se puede eliminar al administrador principal', 'danger')
        return redirect(url_for('admin.admin_admins'))
    
    if target_admin.role != 'admin':
        flash('El usuario no es un administrador', 'danger')
        return redirect(url_for('admin.admin_admins'))
    
    users_created = User.query.filter_by(created_by=target_admin.id).all()
    for user in users_created:
        SensorData.query.filter_by(user_id=user.id).delete()
    
    User.query.filter_by(created_by=target_admin.id).delete()
    db.session.delete(target_admin)
    db.session.commit()
    
    flash('Administrador eliminado correctamente', 'success')
    return redirect(url_for('admin.admin_admins'))

# ==================== REPORTES ====================

@admin_bp.route('/user-reports')
@login_required
def admin_user_reports():
    if current_user.is_root_admin():
        users = User.query.filter_by(role='user', is_active=True, is_deleted=False).all()
    else:
        users = User.query.filter_by(role='user', is_active=True, is_deleted=False).all()
    
    user_reports = []
    for user in users:
        week_ago = datetime.utcnow() - timedelta(days=7)
        user_data = SensorData.query.filter(
            SensorData.user_id == user.id,
            SensorData.timestamp >= week_ago
        ).all()
        
        total_readings = len(user_data)
        alert_readings = len([d for d in user_data if d.is_alert])
        avg_bpm = sum([d.bpm for d in user_data]) / total_readings if total_readings > 0 else 0
        
        if total_readings == 0:
            status = "Sin datos"
            status_class = "secondary"
        elif alert_readings / total_readings < 0.1:
            status = "Excelente"
            status_class = "success"
        elif alert_readings / total_readings < 0.3:
            status = "Estable"
            status_class = "warning"
        else:
            status = "Necesita atención"
            status_class = "danger"
        
        user_reports.append({
            'user': user,
            'total_readings': total_readings,
            'alert_readings': alert_readings,
            'avg_bpm': round(avg_bpm, 1),
            'status': status,
            'status_class': status_class,
            'last_reading': user_data[0].timestamp if user_data else None
        })
    
    return render_template('admin/user_reports.html', user_reports=user_reports)

@admin_bp.route('/user-report/<int:user_id>')
@login_required
def admin_user_detailed_report(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('No se puede ver reporte de administrador', 'danger')
        return redirect(url_for('admin.admin_user_reports'))
    
    if user.is_deleted or not user.is_active:
        flash('No se puede ver reporte de usuario desactivado', 'danger')
        return redirect(url_for('admin.admin_user_reports'))
    
    month_ago = datetime.utcnow() - timedelta(days=30)
    user_data = SensorData.query.filter(
        SensorData.user_id == user.id,
        SensorData.timestamp >= month_ago
    ).order_by(SensorData.timestamp.desc()).all()
    
    total_readings = len(user_data)
    alert_readings = len([d for d in user_data if d.is_alert])
    avg_bpm = sum([d.bpm for d in user_data]) / total_readings if total_readings > 0 else 0
    
    weekly_data = []
    for i in range(4):
        week_start = datetime.utcnow() - timedelta(weeks=(4-i))
        week_end = week_start + timedelta(weeks=1)
        
        week_readings = SensorData.query.filter(
            SensorData.user_id == user.id,
            SensorData.timestamp >= week_start,
            SensorData.timestamp < week_end
        ).all()
        
        week_bpms = [d.bpm for d in week_readings]
        week_avg_bpm = sum(week_bpms) / len(week_bpms) if week_bpms else 0
        week_alerts = len([d for d in week_readings if d.is_alert])
        
        weekly_data.append({
            'week': f"Sem {i+1}",
            'avg_bpm': round(week_avg_bpm, 1),
            'alerts': week_alerts,
            'readings': len(week_readings)
        })
    
    return render_template('admin/user_detailed_report.html',
                         user=user,
                         user_data=user_data,
                         total_readings=total_readings,
                         alert_readings=alert_readings,
                         avg_bpm=avg_bpm,
                         weekly_data=weekly_data,
                         month_ago=month_ago)

# ==================== APIs ====================

@admin_bp.route('/api/stats')
@login_required
def admin_api_stats():
    stats = {
        'total_users': User.query.filter_by(role='user', is_active=True, is_deleted=False).count(),
        'used_devices': Device.query.filter_by(is_used=True).count(),
        'available_devices': Device.query.filter_by(is_used=False).count(),
        'active_alerts': SensorData.query.filter_by(is_alert=True).count()
    }
    return jsonify(stats)

# ✅ ENDPOINT CRÍTICO PARA ESP32 - SIN @login_required
@admin_bp.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """
    Endpoint para recibir datos del ESP32.
    NO requiere autenticación porque el ESP32 no puede usar Flask-Login.
    La seguridad se maneja validando el device_code.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se recibieron datos JSON'}), 400
            
        if 'device_code' not in data or 'bpm' not in data:
            return jsonify({'error': 'Datos incompletos. Se requiere device_code y bpm'}), 400
        
        device_code = data['device_code'].strip().upper()
        bpm = int(data['bpm'])
        
        if bpm < 30 or bpm > 220:
            return jsonify({'error': f'BPM fuera de rango válido: {bpm}'}), 400
        
        user = User.query.filter_by(device_code=device_code).first()
        if not user:
            return jsonify({'error': f'Dispositivo no registrado: {device_code}'}), 404
        
        if not user.is_active or user.is_deleted:
            return jsonify({'error': 'Usuario desactivado'}), 403
        
        max_safe = user.max_safe_bpm or 120
        min_safe = user.min_safe_bpm or 60
        is_alert = bpm > max_safe or bpm < min_safe
        
        sensor_data = SensorData(
            user_id=user.id,
            bpm=bpm,
            is_alert=is_alert,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(sensor_data)
        db.session.commit()
        
        response_data = {
            'message': 'Datos recibidos correctamente',
            'user': user.username,
            'bpm': bpm,
            'is_alert': is_alert,
            'limits': f'{min_safe}-{max_safe} BPM',
            'timestamp': sensor_data.timestamp.isoformat()
        }
        
        if is_alert:
            if bpm > max_safe:
                response_data['alert_message'] = f'ALERTA: Taquicardia ({bpm} > {max_safe} BPM)'
            else:
                response_data['alert_message'] = f'ALERTA: Bradicardia ({bpm} < {min_safe} BPM)'
        
        print(f"✅ Datos recibidos - Usuario: {user.username}, BPM: {bpm}, Alerta: {is_alert}")
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        return jsonify({'error': f'Error en formato de BPM: {str(e)}'}), 400
    except Exception as e:
        print(f"❌ Error en receive_sensor_data: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500