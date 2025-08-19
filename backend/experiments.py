import random
from flask import Blueprint, jsonify, request, g
from auth import require_auth
from db import db_session
from db.models import User
from config import AVAILABLE_EXPERIMENTS

experiments = Blueprint('experiments', __name__)


@experiments.route('/options', methods=['GET'])
@require_auth
def get_options():
    return jsonify({
        'experiments': AVAILABLE_EXPERIMENTS,
        'supportsRandom': True,
        'current': getattr(g, 'current_experiment', None),
    })


@experiments.route('/set', methods=['POST'])
@require_auth
def set_experiment():
    data = request.get_json(force=True) or {}
    requested = data.get('experiment')  # value or 'random'
    # Awareness policy: user is aware for any explicit experiment, unaware if 'random'
    aware = False if requested == 'random' else True

    if requested == 'random':
        chosen = random.choice(AVAILABLE_EXPERIMENTS)
    else:
        if requested not in AVAILABLE_EXPERIMENTS:
            return jsonify({'error': 'invalid experiment'}), 400
        chosen = requested

    with db_session() as session:
        user = session.get(User, g.current_user_id)
        if not user:
            return jsonify({'error': 'user not found'}), 404
        user.current_experiment = chosen
        user.aware_of_experiment = aware

    # update request context for remainder of this request
    g.current_experiment = chosen

    # response hides choice if not aware
    response_choice = chosen if aware else None
    return jsonify({'ok': True, 'current': response_choice})


