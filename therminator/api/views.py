from datetime import datetime, time, timedelta
from flask import jsonify, request
from flask_login import current_user, login_required
from http import HTTPStatus
import pytz
import re
from sqlalchemy.exc import IntegrityError

from .. import app, db, login_manager
from ..exc import ApiError
from ..models import User, Home, Sensor, Reading

@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            app.logger.info('User {!r} authenticated with API'.format(user.email))
            return user
    if wants_json():
        raise ApiError(
            'Please include a valid API key in the Authorization header.',
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    return None

@app.route('/api/v1/<uuid:sensor_uuid>/readings/<date:date>')
@login_required
def api_v1_list_readings(sensor_uuid, date):
    app.logger.info('List readings for sensor {} on {}'.format(sensor_uuid, date))
    sensor = db.session.query(Sensor).filter_by(uuid=sensor_uuid) \
        .join(Home).filter_by(user_id=current_user.id).first_or_404()
    timezone = pytz.timezone(sensor.home.timezone)
    midnight = timezone.localize(datetime.combine(date, time())) \
        .astimezone(pytz.utc).replace(tzinfo=None)
    readings = sensor.readings.filter(Reading.timestamp.between(
        midnight,
        midnight + timedelta(days=1)
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
        app.logger.info('Created reading with {}'.format(data))
        return jsonify({'status': 'Created'}), HTTPStatus.CREATED
    except (IntegrityError, ValueError) as e:
        if re.search(r'Key \(.*\) already exists', e.args[0]):
            message = 'A conflicting record already exists.'
            status_code = HTTPStatus.CONFLICT
        else:
            message = e.args[0]
            status_code = HTTPStatus.UNPROCESSABLE_ENTITY
        app.logger.warning('Failed to create reading: {}'.format(e.args[0]))
        raise ApiError(message, status_code=status_code) from e


def wants_json():
    types = request.accept_mimetypes
    best = types.best_match(['application/json', 'text/html'])
    return best == 'application/json' or types[best] > types['text/html']
