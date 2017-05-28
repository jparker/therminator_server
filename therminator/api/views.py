from http import HTTPStatus
from flask import jsonify, request
from flask_login import login_required
from .. import app, login_manager
from ..models import User
from ..exc import ApiError

@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            app.logger.info('User %s authenticated via API' % user.email)
            return user
    if wants_json():
        app.logger.warning('Aborted request with invalid API key')
        raise ApiError(
            'Please include a valid API key in the Authorization header.',
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    return None

@app.route('/api/v1/test')
@login_required
def api_v1_test():
    return jsonify({'status': 'ok'})

def wants_json():
    types = request.accept_mimetypes
    best = types.best_match(['application/json', 'text/html'])
    app.logger.debug('requested mimetype: {}'.format(types))
    return best == 'application/json' or types[best] > types['text/html']
