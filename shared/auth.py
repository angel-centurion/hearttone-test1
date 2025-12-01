from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from shared.models import db, User, Device
from shared.forms import RegistrationForm

auth_bp = Blueprint('auth', __name__)

# ✅ LISTA DE CÓDIGOS DIRECTAMENTE EN EL ARCHIVO
SECURE_DEVICE_CODES = [
    "HR-SENSOR-A1B2-C3D4",
    "HR-SENSOR-E5F6-G7H8", 
    "HR-SENSOR-I9J0-K1L2",
    "HR-SENSOR-M3N4-O5P6",
    "HR-SENSOR-Q7R8-S9T0",
    "HR-SENSOR-U1V2-W3X4",
    "HR-SENSOR-Y5Z6-A7B8",
    "HR-SENSOR-C9D0-E1F2",
    "HR-SENSOR-G3H4-I5J6",
    "HR-SENSOR-K7L8-M9N0",
    "HR-SENSOR-O1P2-Q3R4",
    "HR-SENSOR-S5T6-U7V8",
    "HR-SENSOR-W9X0-Y1Z2",
    "HR-SENSOR-A3B4-C5D6",
    "HR-SENSOR-E7F8-G9H0",
    "HR-SENSOR-I1J2-K3L4",
    "HR-SENSOR-M5N6-O7P8",
    "HR-SENSOR-Q9R0-S1T2",
    "HR-SENSOR-U3V4-W5X6",
    "HR-SENSOR-Y7Z8-A9B0"
]

def is_valid_device_code(code):
    """Verifica si un código de dispositivo es válido"""
    return code in SECURE_DEVICE_CODES

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.role == 'user':
            return redirect(url_for('user.dashboard'))
        else:
            return redirect(url_for('admin.admin_dashboard'))
    
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
        
        # ✅ VALIDACIÓN DIRECTA SIN IMPORTS EXTERNOS
        device_code = form.device_code.data.strip().upper()
        
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
        
        # ✅ CORREGIDO: Si un admin está creando el usuario, asignar created_by
        created_by_id = None
        if current_user.is_authenticated and current_user.role == 'admin':
            created_by_id = current_user.id
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            device_code=device_code,
            role='user',
            created_by=created_by_id  # ✅ Ahora se asigna correctamente
        )
        user.set_password(form.password.data)
        
        device.is_used = True
        
        db.session.add(user)
        if not Device.query.filter_by(device_code=device_code).first():
            db.session.add(device)
        db.session.commit()
        
        flash('¡Cuenta creada exitosamente! Por favor inicia sesión.', 'success')
        return redirect(url_for('user_login'))
    
    return render_template('auth/register.html', form=form)