import os
import sys
sys.path.append('/app')

from flask import Flask, redirect, url_for, render_template, flash, request
from flask_login import LoginManager, current_user, logout_user, login_user
from shared.models import db, User
from shared.forms import LoginForm, RegistrationForm

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
login_manager.login_view = 'user.user_login'  # ✅ Cambiar a blueprint

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ REGISTRAR BLUEPRINTS CON PREFIJO /user
try:
    from user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')
    print("✅ Blueprint de usuario registrado correctamente en /user")
except ImportError as e:
    print(f"❌ Error importando user_routes: {e}")

# ✅ RUTA RAÍZ - REDIRIGE A LOGIN DE USUARIO
@app.route('/')
def index():
    if current_user.is_authenticated and current_user.role == 'user':
        return redirect(url_for('user.dashboard'))  # ✅ Usar blueprint
    return redirect(url_for('user.user_login'))  # ✅ Usar blueprint

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)