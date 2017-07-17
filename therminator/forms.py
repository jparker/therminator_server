from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

class SignInForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password')
    remember = BooleanField('Remember me')
