from flask import render_template
from . import app

@app.route('/')
def hello():
    return render_template('hello.html')
