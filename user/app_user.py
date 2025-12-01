import os
import sys
sys.path.append('/app')

from flask import Flask, redirect, url_for, render_template, flash, request
from flask_login import LoginManager, current_user, logout_user, login_user
from shared.models import db, User
from shared.forms import LoginForm, RegistrationForm  # ✅ Añadir RegistrationForm

app = Flask(__name__,
           template_folder='/app/templates',
           static_folder='/app/static')

app.config['SECRET_KEY'] = 'clave-secreta-user'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/instance/project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de sesión
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'user_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ REGISTRAR BLUEPRINTS
try:
    from user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')
    print("✅ Blueprint de usuario registrado correctamente")
except ImportError as e:
    print(f"❌ Error importando user_routes: {e}")

# ✅ RUTAS DE AUTH PARA USER APP
@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/register', methods=['GET', 'POST'])
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
        
        # Importar la función de validación desde auth
        from shared.auth import is_valid_device_code
        
        if not is_valid_device_code(device_code):
            flash('Código de dispositivo inválido. Use el código exacto de su pulsera.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Verificar si el dispositivo ya está en uso
        from shared.models import Device
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
        return redirect(url_for('user_login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/logout')
def user_logout():
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('user_login'))

@app.route('/')
def index():
    if current_user.is_authenticated and current_user.role == 'user':
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('user_login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)