import os
import sys
sys.path.append('/app')

from flask import Flask, redirect, url_for, render_template, flash
from flask_login import LoginManager, current_user, logout_user
from shared.models import db, User

app = Flask(__name__,
           template_folder='/app/templates',
           static_folder='/app/static')
app.config['SECRET_KEY'] = 'clave-secreta-user'  # o 'clave-secreta-user'
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
login_manager.login_view = 'user_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ IMPORTAR Y REGISTRAR LOS BLUEPRINTS ANTES DE LAS RUTAS
try:
    from user_routes import user_bp
    from shared.auth import auth_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    print("✅ Blueprints de usuario registrados correctamente")
except ImportError as e:
    print(f"❌ Error importando blueprints: {e}")

@app.route('/login', methods=['GET', 'POST'])
def user_login():
    from shared.forms import LoginForm
    from flask_login import login_user
    from flask import request
    
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