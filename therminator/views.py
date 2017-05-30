from datetime import datetime, time, timedelta
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from http import HTTPStatus
import logging
import pytz
from sqlalchemy.exc import IntegrityError
from urllib.parse import urljoin, urlparse

from . import app, db, login_manager
from .exc import ApiError
from .forms import SignInForm
from .models import User, Home, Sensor, Reading

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            app.logger.info('User {!r} authenticated via API'.format(user.email))
            return user
    if wants_json():
        raise ApiError(
            'Please include a valid API key in the Authorization header.',
            status_code=HTTPStatus.UNAUTHORIZED,
        )

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

@app.route('/api/v1/<uuid:sensor_uuid>/readings/<date:date>')
@login_required
def api_v1_list_readings(sensor_uuid, date):
    app.logger.info('Listing readings for {} on {}'.format(sensor_uuid, date))
    sensor = db.session.query(Sensor).filter_by(uuid=sensor_uuid) \
        .join(Home).filter_by(user_id=current_user.id).first_or_404()
    timezone = pytz.timezone(sensor.home.timezone)
    midnight = timezone.localize(datetime.combine(date, time())) \
        .astimezone(pytz.utc).replace(tzinfo=None)
    readings = sensor.readings.filter(Reading.timestamp.between(
        midnight,
        midnight + timedelta(days=1),
    )).order_by(Reading.timestamp)
    return jsonify([r.as_dict() for r in readings])

@app.route('/api/v1/<uuid:sensor_uuid>/readings', methods=['POST'])
@login_required
def api_v1_create_reading(sensor_uuid):
    sensor = db.session.query(Sensor).filter_by(uuid=sensor_uuid) \
        .join(Home).filter_by(user_id=current_user.id).first_or_404()
    sensor = Sensor.query.filter_by(uuid=sensor_uuid).first_or_404()
    data = request.get_json()
    reading = Reading(sensor=sensor, **data)
    try:
        db.session.add(reading)
        db.session.commit()
        return jsonify({'status': 'Created'}), HTTPStatus.CREATED
    except IntegrityError as e:
        app.logger.warning('Failed to create reading: {}'.format(e.args[0]))
        raise ApiError(e.args[0], status_code=HTTPStatus.CONFLICT) from e

def wants_json():
    types = request.accept_mimetypes
    best = types.best_match(['application/json', 'text/html'])
    return best == 'application/json' or types[best] > types['text/html']

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
