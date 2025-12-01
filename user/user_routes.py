from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user, logout_user, login_user
from shared.models import db, User, Device, SensorData
from shared.forms import MedicalDataForm, ProfileForm, LoginForm, RegistrationForm
from shared.chatbot_config import chatbot_manager
from datetime import datetime, timedelta
import random

user_bp = Blueprint('user', __name__)

# ==================== AUTENTICACIÓN ====================

@user_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated and current_user.role == 'user':
        return redirect(url_for('user.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active and user.role == 'user':
            login_user(user)
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('user.dashboard'))
        else:
            flash('Credenciales incorrectas o no es un usuario válido', 'danger')
    
    return render_template('auth/login.html', form=form)

@user_bp.route('/register', methods=['GET', 'POST'])
def user_register():
    if current_user.is_authenticated and current_user.role == 'user':
        return redirect(url_for('user.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('El nombre de usuario ya existe', 'danger')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Validar código de dispositivo
        device_code = form.device_code.data.strip().upper()
        
        from shared.auth import is_valid_device_code
        
        if not is_valid_device_code(device_code):
            flash('Código de dispositivo inválido. Use el código exacto de su pulsera.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Verificar si el dispositivo ya está en uso
        device = Device.query.filter_by(device_code=device_code).first()
        if device and device.is_used:
            flash('Este dispositivo ya está en uso por otro usuario', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Si el dispositivo no existe en BD, crearlo
        if not device:
            device = Device(device_code=device_code)
        
        # Crear usuario
        user = User(
            username=form.username.data,
            email=form.email.data,
            device_code=device_code,
            role='user'
        )
        user.set_password(form.password.data)
        
        device.is_used = True
        
        db.session.add(user)
        if not Device.query.filter_by(device_code=device_code).first():
            db.session.add(device)
        db.session.commit()
        
        flash('¡Cuenta creada exitosamente! Por favor inicia sesión.', 'success')
        return redirect(url_for('user.user_login'))
    
    return render_template('auth/register.html', form=form)

@user_bp.route('/logout')
def user_logout():
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('user.user_login'))

@user_bp.before_request
def restrict_to_user():
    # Excluir las rutas de login, logout y register de la restricción
    if request.endpoint in ['user.user_login', 'user.user_logout', 'user.user_register']:
        return
    
    if not current_user.is_authenticated or current_user.role != 'user' or not current_user.is_active or current_user.is_deleted:
        flash('Acceso denegado o cuenta desactivada', 'danger')
        return redirect(url_for('user.user_login'))

# ==================== DASHBOARD Y PERFIL ====================

@user_bp.route('/dashboard')
@login_required
def dashboard():
    filter_type = request.args.get('filter', 'todas')
    limit = int(request.args.get('limit', 10))
    
    filter_map = {
        'todas': None,
        'alertas': True,
        'normales': False
    }
    
    query = SensorData.query.filter_by(user_id=current_user.id)
    
    if filter_type in filter_map and filter_map[filter_type] is not None:
        query = query.filter_by(is_alert=filter_map[filter_type])
    
    recent_data = query.order_by(SensorData.timestamp.desc()).limit(limit).all()
    
    total_readings = SensorData.query.filter_by(user_id=current_user.id).count()
    alert_count = SensorData.query.filter_by(user_id=current_user.id, is_alert=True).count()
    
    return render_template('user/dashboard.html', 
                         recent_data=recent_data,
                         total_readings=total_readings,
                         alert_count=alert_count,
                         current_filter=filter_type,
                         current_limit=limit)

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        existing_user = User.query.filter(
            User.email == form.email.data, 
            User.id != current_user.id
        ).first()
        
        if existing_user:
            flash('El email ya está en uso por otro usuario', 'danger')
            return render_template('user/profile.html', form=form)
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        if form.password.data:
            current_user.set_password(form.password.data)
        
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/profile.html', form=form)

# ==================== DATOS MÉDICOS ====================

@user_bp.route('/medical-data', methods=['GET', 'POST'])
@login_required
def medical_data():
    form = MedicalDataForm(obj=current_user)
    
    heart_conditions = [
        ('', 'Sin condición específica'),
        ('arritmia', 'Arritmia Cardíaca'),
        ('taquicardia', 'Taquicardia'),
        ('bradicardia', 'Bradicardia'),
        ('hipertension', 'Hipertensión'),
        ('cardiopatia', 'Cardiopatía Isquémica')
    ]
    form.heart_condition.choices = heart_conditions
    
    if form.validate_on_submit():
        current_user.weight = form.weight.data
        current_user.height = form.height.data
        current_user.age = form.age.data
        current_user.heart_condition = form.heart_condition.data
        
        current_user.calculate_safe_limits()
        
        db.session.commit()
        flash('Datos médicos guardados correctamente', 'success')
        return redirect(url_for('user.monitoring'))
    
    return render_template('user/medical_data.html', form=form)

# ==================== MONITOREO ====================

@user_bp.route('/monitoring')
@login_required
def monitoring():
    if not current_user.age or not current_user.weight:
        flash('Complete sus datos médicos primero para activar el monitoreo', 'warning')
        return redirect(url_for('user.medical_data'))
    
    return render_template('user/monitoring.html')

# ==================== REPORTES ====================

@user_bp.route('/health-report')
@login_required
def health_report():
    if not current_user.age or not current_user.weight or not current_user.height:
        flash('Complete sus datos médicos primero para ver su reporte de salud', 'warning')
        return redirect(url_for('user.medical_data'))
    
    filter_type = request.args.get('filter', 'todas')
    days = int(request.args.get('dias', 7))
    
    filter_map = {
        'todas': None,
        'alertas': True,
        'normales': False
    }
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = SensorData.query.filter(
        SensorData.user_id == current_user.id,
        SensorData.timestamp >= start_date
    )
    
    if filter_type in filter_map and filter_map[filter_type] is not None:
        query = query.filter_by(is_alert=filter_map[filter_type])
    
    recent_data = query.order_by(SensorData.timestamp.desc()).all()
    
    total_readings = len(recent_data)
    alert_readings = len([d for d in recent_data if d.is_alert])
    normal_readings = total_readings - alert_readings
    
    alert_percentage = (alert_readings / total_readings * 100) if total_readings > 0 else 0
    normal_percentage = (normal_readings / total_readings * 100) if total_readings > 0 else 0
    
    avg_bpm = sum([d.bpm for d in recent_data]) / total_readings if total_readings > 0 else 0
    
    health_message, health_tips = generate_health_analysis(
        recent_data, 
        current_user, 
        alert_percentage, 
        avg_bpm
    )
    
    return render_template('user/health_report.html',
                         recent_data=recent_data,
                         total_readings=total_readings,
                         alert_readings=alert_readings,
                         normal_readings=normal_readings,
                         alert_percentage=alert_percentage,
                         normal_percentage=normal_percentage,
                         avg_bpm=avg_bpm,
                         health_message=health_message,
                         health_tips=health_tips,
                         current_filter=filter_type,
                         current_days=days,
                         start_date=start_date)

# ==================== GESTIÓN DE CUENTA ====================

@user_bp.route('/deactivate-account', methods=['GET', 'POST'])
@login_required
def deactivate_account():
    if request.method == 'POST':
        confirm_username = request.form.get('confirm_username')
        if confirm_username != current_user.username:
            flash('El nombre de usuario no coincide', 'danger')
            return render_template('user/deactivate_account.html')
        
        current_user.deactivate_account()
        db.session.commit()
        
        logout_user()
        flash('Tu cuenta ha sido desactivada. Puedes contactar al administrador para reactivarla.', 'info')
        return redirect(url_for('user.user_login'))
    
    return render_template('user/deactivate_account.html')

# ==================== GESTIÓN DE LECTURAS ====================

@user_bp.route('/delete-readings', methods=['POST'])
@login_required
def delete_readings():
    deleted_count = SensorData.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash(f'Se eliminaron {deleted_count} lecturas de tu historial', 'success')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/cleanup-readings', methods=['POST'])
@login_required
def cleanup_readings():
    latest_readings = SensorData.query.filter_by(user_id=current_user.id)\
        .order_by(SensorData.timestamp.desc())\
        .limit(100)\
        .all()
    
    if latest_readings:
        keep_ids = [reading.id for reading in latest_readings]
        
        deleted_count = SensorData.query.filter(
            SensorData.user_id == current_user.id,
            ~SensorData.id.in_(keep_ids)
        ).delete()
        
        db.session.commit()
        flash(f'Se eliminaron {deleted_count} lecturas antiguas. Se mantuvieron las 100 más recientes.', 'success')
    else:
        flash('No hay lecturas para limpiar', 'info')
    
    return redirect(url_for('user.dashboard'))

# ==================== APIs ====================

@user_bp.route('/api/real-time-data')
@login_required
def api_real_time_data():
    try:
        latest_data = SensorData.query.filter_by(user_id=current_user.id)\
            .order_by(SensorData.timestamp.desc())\
            .first()
        
        time_ago = datetime.utcnow() - timedelta(minutes=10)
        historical_data = SensorData.query.filter(
            SensorData.user_id == current_user.id,
            SensorData.timestamp >= time_ago
        ).order_by(SensorData.timestamp.asc()).all()
        
        chart_labels = []
        chart_bpm = []
        chart_alerts = []
        
        for data in historical_data:
            chart_labels.append(data.timestamp.strftime('%H:%M:%S'))
            chart_bpm.append(data.bpm)
            chart_alerts.append(data.bpm if data.is_alert else None)
        
        chart_data = {
            'labels': chart_labels,
            'bpm': chart_bpm,
            'alerts': chart_alerts
        }
        
        if latest_data:
            alert_message = None
            if latest_data.is_alert:
                if latest_data.bpm > (current_user.max_safe_bpm or 120):
                    alert_message = f'ALERTA: Taquicardia ({latest_data.bpm} BPM)'
                else:
                    alert_message = f'ALERTA: Bradicardia ({latest_data.bpm} BPM)'
            
            return jsonify({
                'current_bpm': latest_data.bpm,
                'is_alert': latest_data.is_alert,
                'max_safe': current_user.max_safe_bpm or 120,
                'min_safe': current_user.min_safe_bpm or 60,
                'chart_data': chart_data,
                'message': alert_message,
                'timestamp': latest_data.timestamp.isoformat(),
                'total_readings': len(historical_data)
            })
        else:
            return jsonify({
                'current_bpm': None,
                'is_alert': False,
                'max_safe': current_user.max_safe_bpm or 120,
                'min_safe': current_user.min_safe_bpm or 60,
                'chart_data': chart_data,
                'message': 'Esperando datos del sensor...',
                'timestamp': None,
                'total_readings': 0
            })
            
    except Exception as e:
        print(f"❌ Error en api_real_time_data: {str(e)}")
        return jsonify({'error': 'Error obteniendo datos en tiempo real'}), 500

@user_bp.route('/api/chatbot-analysis', methods=['POST'])
@login_required
def api_chatbot_analysis():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        # Obtener datos del usuario para contexto
        user_data = get_user_health_context()
        
        # Obtener respuesta del chatbot real
        bot_response = chatbot_manager.get_response(user_message, user_data)
        
        return jsonify({
            'response': bot_response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error en chatbot: {str(e)}")
        return jsonify({'error': 'Error en el análisis'}), 500

@user_bp.route('/api/weekly-report')
@login_required
def api_weekly_report():
    week_ago = datetime.utcnow() - timedelta(days=7)
    daily_data = []
    
    for i in range(7):
        day_start = week_ago + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        day_readings = SensorData.query.filter(
            SensorData.user_id == current_user.id,
            SensorData.timestamp >= day_start,
            SensorData.timestamp < day_end
        ).all()
        
        day_bpms = [d.bpm for d in day_readings]
        avg_bpm = sum(day_bpms) / len(day_bpms) if day_bpms else 0
        alerts = len([d for d in day_readings if d.is_alert])
        
        daily_data.append({
            'date': day_start.strftime('%d/%m'),
            'avg_bpm': round(avg_bpm, 1),
            'alerts': alerts,
            'readings': len(day_readings)
        })
    
    return jsonify(daily_data)

# ==================== FUNCIONES AUXILIARES ====================

def get_user_health_context():
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_data = SensorData.query.filter(
        SensorData.user_id == current_user.id,
        SensorData.timestamp >= week_ago
    ).order_by(SensorData.timestamp.desc()).all()
    
    total_readings = len(recent_data)
    alert_readings = len([d for d in recent_data if d.is_alert])
    normal_readings = total_readings - alert_readings
    
    bpms = [d.bpm for d in recent_data]
    avg_bpm = sum(bpms) / len(bpms) if bpms else 0
    max_bpm = max(bpms) if bpms else 0
    min_bpm = min(bpms) if bpms else 0
    
    variability = max_bpm - min_bpm if bpms else 0
    
    three_days_ago = datetime.utcnow() - timedelta(days=3)
    recent_bpms = [d.bpm for d in recent_data if d.timestamp >= three_days_ago]
    older_bpms = [d.bpm for d in recent_data if d.timestamp < three_days_ago]
    
    recent_avg = sum(recent_bpms) / len(recent_bpms) if recent_bpms else 0
    older_avg = sum(older_bpms) / len(older_bpms) if older_bpms else 0
    trend = "mejorando" if recent_avg < older_avg else "estable" if recent_avg == older_avg else "empeorando"
    
    return {
        'user_profile': {
            'username': current_user.username,
            'age': current_user.age,
            'weight': current_user.weight,
            'height': current_user.height,
            'heart_condition': current_user.heart_condition,
            'max_safe_bpm': current_user.max_safe_bpm,
            'min_safe_bpm': current_user.min_safe_bpm
        },
        'statistics': {
            'total_readings': total_readings,
            'alert_readings': alert_readings,
            'normal_readings': normal_readings,
            'alert_percentage': (alert_readings / total_readings * 100) if total_readings > 0 else 0,
            'avg_bpm': round(avg_bpm, 1),
            'max_bpm': max_bpm,
            'min_bpm': min_bpm,
            'variability': variability,
            'trend': trend
        },
        'recent_alerts': [
            {
                'bpm': d.bpm,
                'timestamp': d.timestamp.isoformat(),
                'type': 'high' if d.bpm > (current_user.max_safe_bpm or 120) else 'low'
            }
            for d in recent_data if d.is_alert
        ][:10]
    }

def generate_health_analysis(recent_data, user, alert_percentage, avg_bpm):
    messages = []
    tips = []
    
    if alert_percentage < 10:
        messages.append("🎉 ¡Excelente! Tu ritmo cardíaco se mantiene muy estable.")
        tips.append("Continúa con tus buenos hábitos de salud.")
    elif alert_percentage < 30:
        messages.append("👍 Buen trabajo, tu ritmo cardíaco es mayormente estable.")
        tips.append("Mantén un estilo de vida saludable y monitorea regularmente.")
    else:
        messages.append("⚠️ Se han detectado varias anomalías. Es importante prestar atención.")
        tips.append("Considera consultar con un especialista para una evaluación completa.")
    
    if user.heart_condition:
        if user.heart_condition == 'taquicardia':
            if avg_bpm > 100:
                messages.append("🔴 Se detectan valores consistentemente altos. Recomendamos:")
                tips.extend([
                    "Evita el consumo de cafeína y estimulantes",
                    "Practica técnicas de relajación y respiración",
                    "Mantén una hidratación adecuada"
                ])
            else:
                messages.append("💚 Buen control de la taquicardia")
                tips.append("Sigue las recomendaciones de tu cardiólogo")
                
        elif user.heart_condition == 'bradicardia':
            if avg_bpm < 50:
                messages.append("🔵 Se detectan valores consistentemente bajos. Recomendamos:")
                tips.extend([
                    "Realiza actividad física moderada regularmente",
                    "Mantén una alimentación balanceada",
                    "Consulta sobre posibles ajustes medicamentosos"
                ])
            else:
                messages.append("💚 Buen control de la bradicardia")
                tips.append("Continúa con tu seguimiento médico regular")
                
        elif user.heart_condition == 'arritmia':
            bpms = [d.bpm for d in recent_data]
            variability = max(bpms) - min(bpms) if bpms else 0
            
            if variability > 50:
                messages.append("🔄 Alta variabilidad detectada. Recomendamos:")
                tips.extend([
                    "Evita situaciones de estrés intenso",
                    "Mantén un horario regular de sueño",
                    "Registra los episodios para compartir con tu médico"
                ])
            else:
                messages.append("💚 Buena estabilidad del ritmo cardíaco")
                tips.append("Sigue tomando tus medicamentos según indicación")
                
        elif user.heart_condition == 'hipertension':
            messages.append("🩺 Para tu condición de hipertensión:")
            tips.extend([
                "Controla tu consumo de sal",
                "Realiza ejercicio aeróbico regular",
                "Mide tu presión arterial regularmente"
            ])
    
    if avg_bpm > 90:
        tips.append("💡 Considera incorporar meditación o yoga para reducir el estrés")
    elif avg_bpm < 55:
        tips.append("💡 La actividad física moderada puede ayudar a aumentar tu ritmo cardíaco en reposo")
    
    return messages, tips