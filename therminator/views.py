from datetime import datetime, time, timedelta
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
import pytz
from sqlalchemy.exc import IntegrityError
from urllib.parse import urljoin, urlparse

from . import app, db, login_manager
from .forms import SignInForm, SensorForm
from .models import User, Home, Sensor, Reading

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.context_processor
def expose_timedelta():
    def _timedelta(**kwargs):
        return timedelta(**kwargs)
    return dict(timedelta=_timedelta)

@app.template_filter('localtime')
def localtime(timestamp, timezone, fmt='%Y-%m-%d %H:%M %Z'):
    tz = pytz.timezone(timezone)
    local = pytz.utc.localize(timestamp, is_dst=None).astimezone(tz)
    return local.strftime(fmt)

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
            login_user(user, remember=form.remember.data)
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
    return render_template('homes/show.html', home=home)

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
        current_sensor=sensor,
        home=sensor.home,
        readings=readings,
        date=date,
    )

@app.route('/homes/<int:home_id>/sensors/new')
@login_required
def new_sensor(home_id):
    home = current_user.homes.filter_by(id=home_id).first_or_404()
    form = SensorForm()
    return render_template('sensors/new.html', form=form, home=home)

@app.route('/homes/<int:home_id>/sensors', methods=['POST'])
@login_required
def create_sensor(home_id):
    home = current_user.homes.filter_by(id=home_id).first_or_404()
    form = SensorForm()
    if form.validate_on_submit():
        sensor = Sensor(home=home, name=form.name.data)
        db.session.add(sensor)
        db.session.commit()
        flash('Sensor {} created successfully.'.format(sensor.name), 'success')
        return redirect(url_for('show_sensor', sensor_id=sensor.id))
    flash('Sensor could not be created.', 'danger')
    return render_template('sensors/new.html', form=form, home=home)

@app.route('/sensors/<int:sensor_id>/edit')
@login_required
def edit_sensor(sensor_id):
    sensor = db.session.query(Sensor).filter_by(id=sensor_id) \
        .join(Home).filter_by(user_id=current_user.id).first_or_404()
    form = SensorForm()
    form.process(obj=sensor)
    return render_template(
        'sensors/edit.html',
        form=form,
        current_sensor=sensor,
        home=sensor.home,
    )

@app.route('/sensors/<int:sensor_id>', methods=['POST', 'PATCH'])
@login_required
def update_sensor(sensor_id):
    sensor = db.session.query(Sensor).filter_by(id=sensor_id) \
        .join(Home).filter_by(user_id=current_user.id).first_or_404()
    form = SensorForm()
    if form.validate_on_submit():
        sensor.name = form.name.data
        db.session.add(sensor)
        db.session.commit()
        flash('Sensor {} updated successfully.'.format(sensor.name), 'success')
        return redirect(url_for('show_sensor', sensor_id=sensor.id))
    flash('Sensor could not be updated.', 'danger')
    return render_template(
        'sensors/edit.html',
        form=form,
        current_sensor=sensor,
        home=sensor.home,
    )


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
