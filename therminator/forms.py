from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

class SignInForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password')
    remember = BooleanField('Remember me')

class RefreshSessionForm(FlaskForm):
    password = PasswordField('Password')

class SensorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
