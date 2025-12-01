import os
import sys
sys.path.append('/app')

from flask import Flask, redirect, url_for, render_template, flash
from flask_login import LoginManager, current_user, logout_user
from shared.models import db, User, Device

app = Flask(__name__, 
           template_folder='/app/templates',
           static_folder='/app/static')

app.config['SECRET_KEY'] = 'clave-secreta-admin'
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
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ REGISTRAR SOLO EL BLUEPRINT DE ADMIN
try:
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    print("✅ Blueprint de admin registrado correctamente")
except ImportError as e:
    print(f"❌ Error importando admin_routes: {e}")

# ✅ RUTAS DE AUTH PARA ADMIN APP
@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    from shared.forms import LoginForm
    from flask_login import login_user
    from flask import request
    
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

@app.route('/logout')
def admin_logout():
    logout_user()
    flash('Has cerrado sesión de administrador', 'info')
    return redirect(url_for('admin_login'))

@app.route('/')
def index():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    return redirect(url_for('admin_login'))

def initialize_database():
    with app.app_context():
        try:
            print("🗑️  Eliminando tablas existentes...")
            db.drop_all()  # Forzar eliminación
            
            print("🔄 Creando nuevas tablas...")
            db.create_all()  # Crear desde cero
            
            # Verificar columnas creadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            print(f"✅ Columnas de users: {columns}")
            
            # Crear admin principal
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@system.com',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                print("✅ Admin principal creado: usuario='admin', contraseña='admin123'")
            
            # Crear dispositivos
            from shared.auth import SECURE_DEVICE_CODES
            for code in SECURE_DEVICE_CODES:
                if not Device.query.filter_by(device_code=code).first():
                    device = Device(device_code=code)
                    db.session.add(device)
                    print(f"  + Dispositivo: {code}")
            
            db.session.commit()
            print("🎉 Base de datos inicializada CORRECTAMENTE")
            
        except Exception as e:
            print(f"❌ Error crítico: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True, host='0.0.0.0', port=5000)