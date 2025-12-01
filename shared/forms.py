from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired()])
    device_code = StringField('Código del Dispositivo', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Registrarse')

class CreateAdminForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired()])
    submit = SubmitField('Crear Administrador')

class ProfileForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Nueva Contraseña (dejar vacío para no cambiar)',
                           validators=[Optional(), Length(min=6)])
    submit = SubmitField('Actualizar Perfil')

class MedicalDataForm(FlaskForm):
    weight = FloatField('Peso (kg)', validators=[DataRequired(), NumberRange(min=20, max=200)])
    height = FloatField('Altura (m)', validators=[DataRequired(), NumberRange(min=0.5, max=2.5)])
    age = IntegerField('Edad', validators=[DataRequired(), NumberRange(min=1, max=120)])
    heart_condition = SelectField('Condición Cardíaca', validators=[Optional()])
    submit = SubmitField('Guardar Datos Médicos')