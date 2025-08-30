import random
from typing import List
from flask import Blueprint, jsonify, request, g
from sqlalchemy import and_, select, func
from auth import require_auth
from config import BATCH_SIZE, AI_POSTS_RATIO
from db import db_session
from db.models import Post, ServedPost, HumorPost
from generate import get_ai_posts
from stats import increment_ai_post_count, increment_real_post_count

feed = Blueprint('feed', __name__)


def sample_random_posts_excluding_served(user_id: int, limit: int, source: str) -> List[Post]:
    # Two-phase sampling using random_key windows to avoid ORDER BY RANDOM() cost
    # 1) try to pick a random window and fetch LIMIT rows not served
    # 2) if insufficient, fall back to a few retries; finally fallback to ORDER BY RANDOM for small remainder
    results: List[Post] = []
    attempts = 5
    with db_session() as session:
        for _ in range(attempts):
            # Pick a random center and clamp window within signed BIGINT range
            center = random.getrandbits(63)  # [0, 2^63-1]
            half_span = 1 << 59  # keep total span at 2^60
            min_bigint = 0
            max_bigint = (1 << 63) - 1
            a = center - half_span if center >= half_span else min_bigint
            b = center + half_span if center <= (max_bigint - half_span) else max_bigint
            if source == 'humorposts':
                q = (
                    session.query(HumorPost)
                    .order_by(func.random())
                    .limit(limit - len(results))
                )
            else:
                q = (
                    session.query(Post)
                    .outerjoin(ServedPost, and_(ServedPost.user_id == user_id, ServedPost.post_id == Post.id))
                    .filter(
                        Post.random_key.between(a, b),
                        ServedPost.id.is_(None),
                    )
                    .limit(limit - len(results))
                )
            chunk = q.all()
            results.extend(chunk)
            if len(results) >= limit:
                break

        if len(results) < limit:
            # Fallback: simple random order for the remainder
            remainder = limit - len(results)
            if source == 'humorposts':
                q = (
                    session.query(HumorPost)
                    .order_by(func.random())
                    .limit(remainder * 2)
                )
            else:
                q = (
                    session.query(Post)
                    .outerjoin(ServedPost, and_(ServedPost.user_id == user_id, ServedPost.post_id == Post.id))
                    .filter(ServedPost.id.is_(None))
                    .order_by(Post.random_key)
                    .limit(remainder * 10)
                )
            pool = q.all()
            random.shuffle(pool)
            results.extend(pool[:remainder])

        # Mark served only for posts (reverting humor marking)
        if source != 'humorposts':
            for p in results:
                session.add(ServedPost(user_id=user_id, post_id=p.id))

    return results


@feed.route('/feed')
@require_auth
def get_feed():
    limit = int(request.args.get('limit') or BATCH_SIZE)
    user_id = g.current_user_id
    source = request.args.get('source') or 'posts'
    if source not in ('posts', 'humorposts'):
        source = 'posts'
    posts = sample_random_posts_excluding_served(user_id, limit, source)

    # Map to response schema
    def to_dict(p):
        return {
            'id': p.id,
            'title': p.title,
            'self_text': p.self_text,
            'subreddit': p.subreddit,
            'over_18': 'true' if getattr(p, 'over_18', False) else 'false',
            'link_flair_text': getattr(p, 'link_flair_text', None),
            'is_ai': bool(getattr(p, 'is_ai', False)),
        }
    resp_posts = [to_dict(p) for p in posts]
    # If source is humor, include humor_id to enable interactions
    if request.args.get('source') == 'humorposts':
        for i, p in enumerate(posts):
            resp_posts[i]['humor_id'] = p.id

    # Interleave AI posts up to the requested ratio
    desired_ai = max(0, min(len(posts), int(round(len(posts) * AI_POSTS_RATIO))))
    ai_posts = get_ai_posts()[:desired_ai]
    for ai in ai_posts:
        idx = random.randint(0, len(resp_posts))
        resp_posts.insert(idx, ai)

    # Update served counters: real posts and AI posts served
    for _ in range(len(posts)):
        increment_real_post_count()
    for _ in range(len(ai_posts)):
        increment_ai_post_count()

    return jsonify({
        'posts': resp_posts,
        'count': len(resp_posts),
        'batchIndex': 0,
        'skippedInvalidPosts': 0,
        'totalProcessedRows': 0,
        'endOfFile': False,
        'batchSize': limit,
        'aiPostsCount': len(ai_posts),
    })


