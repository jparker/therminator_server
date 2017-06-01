from datetime import datetime, time, timedelta
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from http import HTTPStatus
import logging
import pytz
import re
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

@app.context_processor
def expose_timedelta():
    def _timedelta(**kwargs):
        return timedelta(**kwargs)
    return dict(timedelta=_timedelta)

@app.template_filter('localtime')
def localtime(timestamp, timezone):
    tz = pytz.timezone(timezone)
    local = pytz.utc.localize(timestamp, is_dst=None).astimezone(tz)
    return local.strftime('%H:%M %Z')

@app.template_filter('numerify')
def numerify(number, prec=1):
    return '{:,.{prec}f}'.format(number, prec=prec)

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
            return redirect_back('list_homes')
        else:
            app.logger.warning('User {!r} failed to sign in'.format(form.email.data))
            flash('Invalid email address or password.', 'danger')
    return render_template('sign_in.html', form=form, target=target)

@app.route('/sign-out', methods=['GET', 'DELETE'])
def sign_out():
    app.logger.info('User {!r} signed out'.format(current_user.email))
    logout_user()
    flash('You have successfully signed out.', 'info')
    return redirect(url_for('list_homes'))

@app.route('/')
@login_required
def list_homes():
    return render_template('homes/index.html', homes=current_user.homes)

@app.route('/homes/<int:home_id>')
@login_required
def show_home(home_id):
    home = current_user.homes.filter_by(id=home_id).first_or_404()
    return render_template('homes/show.html', home=home, sensors=home.sensors)

@app.route('/sensors/<int:sensor_id>', defaults={'date': None})
@app.route('/sensors/<int:sensor_id>/<date:date>')
@login_required
def show_sensor(sensor_id, date):
    sensor = db.session.query(Sensor).filter_by(id=sensor_id) \
        .join(Home).filter_by(user_id=current_user.id).first_or_404()
    timezone = pytz.timezone(sensor.home.timezone)
    if not date:
        date = datetime.now(timezone).date()
    midnight = timezone.localize(datetime.combine(date, time())) \
        .astimezone(pytz.utc).replace(tzinfo=None)
    readings = sensor.readings.filter(Reading.timestamp.between(
        midnight,
        midnight + timedelta(days=1),
    )).order_by(Reading.timestamp)
    return render_template(
        'sensors/show.html',
        sensor=sensor,
        home=sensor.home,
        readings=readings,
        date=date,
    )

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
    data = request.get_json()
    try:
        reading = Reading(sensor=sensor, **data)
        db.session.add(reading)
        db.session.commit()
        return jsonify({'status': 'Created'}), HTTPStatus.CREATED
    except (IntegrityError, ValueError) as e:
        app.logger.warning('Failed to create reading: {}'.format(e.args[0]))
        if re.search(r'Key \(.*\) already exists', e.args[0]):
            message = 'A conflicting record already exists.'
            status_code = HTTPStatus.CONFLICT
        else:
            message = e.args[0]
            status_code = HTTPStatus.UNPROCESSABLE_ENTITY
        raise ApiError(message, status_code=status_code) from e

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
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, url))
    return test_url.scheme in ('http', 'https') \
        and ref_url.netloc == test_url.netloc
