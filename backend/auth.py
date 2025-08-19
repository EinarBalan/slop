import datetime
import hashlib
from functools import wraps
from typing import Optional
import jwt
from flask import Blueprint, request, jsonify, g
from config import SECRET_KEY, DEV_AUTH_NO_PASSWORD
from db import db_session
from db.models import User
from sqlalchemy.exc import IntegrityError

auth = Blueprint('auth', __name__)


def hash_password(password: str) -> str:
    # Simple sha256 for now; swap to bcrypt/argon2 later
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_user_if_missing(username: str, password: Optional[str] = None) -> User:
    with db_session() as session:
        user = session.query(User).filter_by(username=username).first()
        if user is None:
            user = User(username=username)
            if password:
                user.password_hash = hash_password(password)
            session.add(user)
            try:
                session.flush()
            except IntegrityError:
                session.rollback()
                # Another concurrent request created the user; fetch and return it
                user = session.query(User).filter_by(username=username).first()
        return user


def authenticate_user(username: str, password: Optional[str]) -> Optional[User]:
    with db_session() as session:
        user = session.query(User).filter_by(username=username).first()
        if user is None:
            return None
        if user.password_hash is None:
            # dev users may not have password set
            return user
        if password and user.password_hash == hash_password(password):
            return user
        return None


def generate_jwt(user: User) -> str:
    now = datetime.datetime.utcnow()
    # Backdate iat slightly to avoid clock skew issues across processes/threads
    payload = {
        'sub': user.id,
        'username': user.username,
        'iat': int((now - datetime.timedelta(seconds=5)).timestamp()),
        'exp': int((now + datetime.timedelta(hours=12)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = (data or {}).get('username')
    password = (data or {}).get('password')
    if not username:
        return jsonify({'error': 'username required'}), 400

    if DEV_AUTH_NO_PASSWORD:
        user = create_user_if_missing(username, password)
    else:
        user = authenticate_user(username, password)
        if user is None:
            return jsonify({'error': 'invalid credentials'}), 401

    token = generate_jwt(user)
    return jsonify({'token': token, 'user': {'id': user.id, 'username': user.username}})


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization')
        if not header or not header.startswith('Bearer '):
            return jsonify({'error': 'missing bearer token'}), 401
        token = header.split(' ', 1)[1]
        try:
            # Allow small clock skew and skip iat validation; still verify signature/exp
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=['HS256'],
                leeway=60,
                options={
                    'verify_iat': False,
                }
            )
            user_id = payload.get('sub')
        except Exception as e:
            return jsonify({'error': 'invalid token', 'message': str(e)}), 401
        with db_session() as session:
            user = session.get(User, user_id)
            if not user:
                return jsonify({'error': 'user not found'}), 401
            g.current_user_id = user.id
            g.current_experiment = user.current_experiment
            g.current_user_aware = user.aware_of_experiment
        return fn(*args, **kwargs)
    return wrapper


