from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_wtf.file import FileField, FileAllowed, FileRequired
class RegisterForm(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired()])
    email = StringField("Correo electrónico", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    confirm_password = PasswordField("Confirmar contraseña", validators=[
        DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')
    ])
    submit = SubmitField("Registrar")

class LoginForm(FlaskForm):
    username = StringField("Nombre de usuario", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Iniciar sesión")

class UploadFaceForm(FlaskForm):
    person_name = StringField("Nombre del rostro", validators=[DataRequired()])
    image = FileField("Imagen del rostro", validators=[
        FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Solo imágenes.')
    ])
    submit = SubmitField("Subir rostro")

class FaceVerificationForm(FlaskForm):
    image = FileField("Imagen a verificar", validators=[
        FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'], 'Solo imágenes.')
    ])
    submit = SubmitField("Verificar rostro")

