from config import args
from flask import g
from db import db_session
from db.models import Experiment

# In-process counters (not persisted) – optional debugging only
AI_POST_COUNT = 0
LIKED_AI_POST_COUNT = 0
REAL_POST_COUNT = 0
LIKED_REAL_POST_COUNT = 0
AI_MARKED_AS_AI_COUNT = 0
REAL_MARKED_AS_AI_COUNT = 0
AI_DISLIKE_COUNT = 0
REAL_DISLIKE_COUNT = 0

def _update_experiment_counts(ai_delta: int = 0, liked_ai_delta: int = 0, real_delta: int = 0, liked_real_delta: int = 0,
                              ai_marked_delta: int = 0, real_marked_delta: int = 0,
                              ai_dislike_delta: int = 0, real_dislike_delta: int = 0) -> None:
    """Cumulatively update experiment counters for the current user/experiment.

    Creates the row if missing and recomputes like rates.
    """
    try:
        with db_session() as session:
            current_user_id = getattr(g, 'current_user_id', None)
            current_experiment = getattr(g, 'current_experiment', None)
            current_aware = getattr(g, 'current_user_aware', None)
            if current_user_id is None:
                return
            experiment_name = current_experiment or 'base'
            exp = session.query(Experiment).filter_by(experiment=experiment_name, user_id=current_user_id).one_or_none()
            if exp is None:
                exp = Experiment(
                    experiment=experiment_name,
                    user_id=current_user_id,
                )
                session.add(exp)
                session.flush()

            # Apply deltas
            if ai_delta:
                exp.ai_post_count = (exp.ai_post_count or 0) + int(ai_delta)
            if liked_ai_delta:
                exp.liked_ai_post_count = (exp.liked_ai_post_count or 0) + int(liked_ai_delta)
            if real_delta:
                exp.real_post_count = (exp.real_post_count or 0) + int(real_delta)
            if liked_real_delta:
                exp.liked_real_post_count = (exp.liked_real_post_count or 0) + int(liked_real_delta)
            if ai_marked_delta:
                exp.ai_marked_as_ai_count = (exp.ai_marked_as_ai_count or 0) + int(ai_marked_delta)
            if real_marked_delta:
                exp.real_marked_as_ai_count = (exp.real_marked_as_ai_count or 0) + int(real_marked_delta)
            if ai_dislike_delta:
                exp.ai_dislike_count = (exp.ai_dislike_count or 0) + int(ai_dislike_delta)
            if real_dislike_delta:
                exp.real_dislike_count = (exp.real_dislike_count or 0) + int(real_dislike_delta)

            # Recompute like rates
            exp.ai_like_rate = (exp.liked_ai_post_count / exp.ai_post_count) if exp.ai_post_count > 0 else 0
            exp.real_like_rate = (exp.liked_real_post_count / exp.real_post_count) if exp.real_post_count > 0 else 0
            exp.ai_marked_as_ai_rate = (exp.ai_marked_as_ai_count / exp.ai_post_count) if exp.ai_post_count > 0 else 0
            exp.real_marked_as_ai_rate = (exp.real_marked_as_ai_count / exp.real_post_count) if exp.real_post_count > 0 else 0
            exp.ai_dislike_rate = (exp.ai_dislike_count / exp.ai_post_count) if exp.ai_post_count > 0 else 0
            exp.real_dislike_rate = (exp.real_dislike_count / exp.real_post_count) if exp.real_post_count > 0 else 0

            if current_aware is not None:
                exp.aware_of_experiment = bool(current_aware)
    except Exception as e:
        print(f"Failed to persist experiment stats to DB: {e}")


def increment_ai_post_count(amount: int = 1):
    global AI_POST_COUNT
    AI_POST_COUNT += amount
    _update_experiment_counts(ai_delta=amount)


def increment_liked_ai_post_count(amount: int = 1):
    global LIKED_AI_POST_COUNT
    LIKED_AI_POST_COUNT += amount
    _update_experiment_counts(liked_ai_delta=amount)


def increment_real_post_count(amount: int = 1):
    global REAL_POST_COUNT
    REAL_POST_COUNT += amount
    _update_experiment_counts(real_delta=amount)


def increment_liked_real_post_count(amount: int = 1):
    global LIKED_REAL_POST_COUNT
    LIKED_REAL_POST_COUNT += amount
    _update_experiment_counts(liked_real_delta=amount)


def increment_marked_as_ai(is_ai_post: bool, amount: int = 1):
    global AI_MARKED_AS_AI_COUNT, REAL_MARKED_AS_AI_COUNT
    if is_ai_post:
        AI_MARKED_AS_AI_COUNT += amount
        _update_experiment_counts(ai_marked_delta=amount)
    else:
        REAL_MARKED_AS_AI_COUNT += amount
        _update_experiment_counts(real_marked_delta=amount)


def increment_dislike(is_ai_post: bool, amount: int = 1):
    global AI_DISLIKE_COUNT, REAL_DISLIKE_COUNT
    if is_ai_post:
        AI_DISLIKE_COUNT += amount
        _update_experiment_counts(ai_dislike_delta=amount)
    else:
        REAL_DISLIKE_COUNT += amount
        _update_experiment_counts(real_dislike_delta=amount)

