from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    device_code = db.Column(db.String(50), unique=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Datos médicos
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    heart_condition = db.Column(db.String(100))
    age = db.Column(db.Integer)
    max_safe_bpm = db.Column(db.Integer, default=120)
    min_safe_bpm = db.Column(db.Integer, default=60)
    
    # Relación para saber qué usuarios creó este admin
    created_users = db.relationship('User', backref=db.backref('creator', remote_side=[id]))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def calculate_safe_limits(self):
        """Calcular límites seguros basados en datos médicos"""
        if self.age and self.heart_condition:
            base_max = 220 - self.age
            
            if self.heart_condition == 'arritmia':
                self.max_safe_bpm = int(base_max * 0.7)
                self.min_safe_bpm = 50
            elif self.heart_condition == 'taquicardia':
                self.max_safe_bpm = int(base_max * 0.6)
                self.min_safe_bpm = 60
            elif self.heart_condition == 'bradicardia':
                self.max_safe_bpm = int(base_max * 0.8)
                self.min_safe_bpm = 40
            else:
                self.max_safe_bpm = int(base_max * 0.85)
                self.min_safe_bpm = 55

    def is_root_admin(self):
        return self.username == 'admin' and self.created_by is None

    def can_deactivate_user(self, target_user):
        if self.role != 'admin':
            return False
        
        if self.is_root_admin():
            return True
        
        if target_user.role == 'user' and target_user.created_by == self.id:
            return True
        
        return False

    def deactivate_account(self):
        """Desactivar la cuenta en lugar de borrarla"""
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        
        if self.device_code:
            device = Device.query.filter_by(device_code=self.device_code).first()
            if device:
                device.is_used = False

    def reactivate_account(self):
        """Reactivar una cuenta desactivada"""
        self.is_active = True
        self.is_deleted = False
        self.deleted_at = None
        
        if self.device_code:
            device = Device.query.filter_by(device_code=self.device_code).first()
            if device:
                device.is_used = True

    @property
    def is_authenticated(self):
        return self.is_active and not self.is_deleted

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(50), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bpm = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_alert = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('sensor_data', lazy=True))