from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os
from .converters import DateConverter, UUIDConverter

app = Flask(__name__)
app_settings = os.getenv('APP_SETTINGS', 'therminator.config.Development')
app.config.from_object(app_settings)

app.url_map.converters['date'] = DateConverter
app.url_map.converters['uuid'] = UUIDConverter

db = SQLAlchemy(app)
migrate = Migrate(app, db)

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)

import therminator.views
