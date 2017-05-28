from flask import Flask
import os

app = Flask(__name__)
app_settings = os.getenv('APP_SETTINGS', 'therminator.config.Development')
app.config.from_object(app_settings)

import therminator.views
