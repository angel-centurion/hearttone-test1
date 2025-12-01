import os
import sys
sys.path.append('/app')

from flask import Flask, redirect, url_for, render_template, flash
from flask_login import LoginManager, current_user, logout_user
from shared.models import db, User, Device

app = Flask(__name__, 
           template_folder='/app/templates',
           static_folder='/app/static')

app.config['SECRET_KEY'] = 'clave-secreta-admin'  # o 'clave-secreta-user'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/instance/project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ CONFIGURACIÓN MEJORADA DE SESIÓN
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora
app.config['SESSION_COOKIE_SECURE'] = False  # True en producción con HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ IMPORTAR Y REGISTRAR EL BLUEPRINT
try:
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    print("✅ Blueprint de admin registrado correctamente")
except ImportError as e:
    print(f"❌ Error importando admin_routes: {e}")

@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    from shared.forms import LoginForm
    from flask_login import login_user
    from flask import request
    from shared.models import User
    
    # ✅ Si ya está autenticado, redirigir inmediatamente
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active and user.role == 'admin':
            # ✅ FORZAR LA SESIÓN para evitar problemas de login
            login_user(user, remember=True, force=True)
            
            # ✅ Confirmar la sesión inmediatamente
            from flask import session
            session.permanent = True
            
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
        return redirect(url_for('admin.admin_dashboard'))  # ✅ CORREGIDO
    return redirect(url_for('admin_login'))

def initialize_database():
    with app.app_context():
        try:
            db.create_all()
            
            # Verificar si la tabla users tiene la columna created_by
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'created_by' not in columns:
                print("⚠️  La base de datos necesita ser recreada. Elimina instance/project.db y reinicia.")
                return
            
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@system.com',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                print("✅ Admin principal creado: usuario='admin', contraseña='admin123'")
            
            # ✅ CORREGIDO: PRIMERO ELIMINAR DISPOSITIVOS ANTIGUOS
            old_devices = Device.query.filter(Device.device_code.like('DEVICE_%')).all()
            if old_devices:
                print(f"🗑️  Eliminando {len(old_devices)} dispositivos antiguos...")
                for device in old_devices:
                    print(f"  - Eliminado: {device.device_code}")
                    db.session.delete(device)
                db.session.commit()
            
            # ✅ LISTA DE CÓDIGOS SEGUROS
            SECURE_DEVICE_CODES = [
                "HR-SENSOR-A1B2-C3D4", "HR-SENSOR-E5F6-G7H8", "HR-SENSOR-I9J0-K1L2",
                "HR-SENSOR-M3N4-O5P6", "HR-SENSOR-Q7R8-S9T0", "HR-SENSOR-U1V2-W3X4",
                "HR-SENSOR-Y5Z6-A7B8", "HR-SENSOR-C9D0-E1F2", "HR-SENSOR-G3H4-I5J6",
                "HR-SENSOR-K7L8-M9N0", "HR-SENSOR-O1P2-Q3R4", "HR-SENSOR-S5T6-U7V8",
                "HR-SENSOR-W9X0-Y1Z2", "HR-SENSOR-A3B4-C5D6", "HR-SENSOR-E7F8-G9H0",
                "HR-SENSOR-I1J2-K3L4", "HR-SENSOR-M5N6-O7P8", "HR-SENSOR-Q9R0-S1T2",
                "HR-SENSOR-U3V4-W5X6", "HR-SENSOR-Y7Z8-A9B0"
            ]
            
            # ✅ CONTAR SOLO DISPOSITIVOS NUEVOS
            new_devices_count = Device.query.filter(Device.device_code.like('HR-SENSOR-%')).count()
            print(f"DEBUG: Dispositivos nuevos existentes: {new_devices_count}")
            
            # Si ya hay 20 dispositivos NUEVOS, no hacer nada
            if new_devices_count >= 20:
                print("✅ Ya existen 20 dispositivos nuevos, no se crean más")
            else:
                # Crear solo los dispositivos nuevos que faltan
                existing_codes = [d.device_code for d in Device.query.all()]
                new_devices_created = 0
                
                for code in SECURE_DEVICE_CODES:
                    if code not in existing_codes:
                        device = Device(device_code=code)
                        db.session.add(device)
                        new_devices_created += 1
                        print(f"  + Creado: {code}")
                
                db.session.commit()
                print(f"✅ {new_devices_created} dispositivos nuevos creados")
            
            # ✅ VERIFICACIÓN FINAL
            total_devices = Device.query.count()
            new_devices_final = Device.query.filter(Device.device_code.like('HR-SENSOR-%')).count()
            old_devices_final = Device.query.filter(Device.device_code.like('DEVICE_%')).count()
            
            print(f"📊 ESTADO FINAL:")
            print(f"  - Dispositivos totales: {total_devices}")
            print(f"  - Dispositivos nuevos: {new_devices_final}")
            print(f"  - Dispositivos antiguos: {old_devices_final}")
            
            if total_devices == 20 and old_devices_final == 0:
                print("✅ ✅ ¡SISTEMA LIMPIO! Exactamente 20 dispositivos nuevos")
            else:
                print(f"⚠️  ADVERTENCIA: Configuración inesperada")
            
            print("✅ Base de datos inicializada correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True, host='0.0.0.0', port=5000)