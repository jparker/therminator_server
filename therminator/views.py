from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
import logging
from urllib.parse import urljoin, urlparse

from . import app, login_manager
from .forms import SignInForm
from .models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def hello():
    return render_template('hello.html')

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    form = SignInForm()
    target = get_redirect_target()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_correct_password(form.password.data):
            app.logger.info('User {!r} signed in'.format(user.email))
            login_user(user)
            flash('You have successfully signed in.', 'success')
            return redirect_back('hello')
        else:
            app.logger.warning('User {!r} failed to sign in'.format(form.email.data))
            flash('Invalid email address or password.', 'danger')
    return render_template('sign_in.html', form=form)

@app.route('/sign-out', methods=['GET', 'DELETE'])
def sign_out():
    app.logger.info('User {!r} signed out'.format(current_user.email))
    logout_user()
    flash('You have successfully signed out.', 'info')
    return redirect(url_for('hello'))


def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target
    return None

def redirect_back(default, **params):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(default, **params)
    return redirect(target)

def is_safe_url(url):
    ref_url = urlparse(request.host_url, url)
    test_url = urlparse(urljoin(request.host_url, url))
    return test_url.scheme in ('http', 'https') \
        and ref_url.netloc == test_url.netloc
