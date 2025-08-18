import random
from typing import List
from flask import Blueprint, jsonify, request, g
from sqlalchemy import and_, select
from auth import require_auth
from config import BATCH_SIZE, AI_POSTS_RATIO
from db import db_session
from db.models import Post, ServedPost
from generate import get_ai_posts

feed = Blueprint('feed', __name__)


def sample_random_posts_excluding_served(user_id: int, limit: int) -> List[Post]:
    # Two-phase sampling using random_key windows to avoid ORDER BY RANDOM() cost
    # 1) try to pick a random window and fetch LIMIT rows not served
    # 2) if insufficient, fall back to a few retries; finally fallback to ORDER BY RANDOM for small remainder
    results: List[Post] = []
    attempts = 5
    with db_session() as session:
        for _ in range(attempts):
            a = random.getrandbits(63)
            b = a + (1 << 60)  # large span; SQLite will clamp
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

        # Mark served
        for p in results:
            session.add(ServedPost(user_id=user_id, post_id=p.id))

    return results


@feed.route('/feed')
@require_auth
def get_feed():
    limit = int(request.args.get('limit') or BATCH_SIZE)
    user_id = g.current_user_id
    posts = sample_random_posts_excluding_served(user_id, limit)

    # Map to response schema
    resp_posts = [
        {
            'title': p.title,
            'self_text': p.self_text,
            'subreddit': p.subreddit,
            'post_id': p.post_id or str(p.id),
            'over_18': 'true' if p.over_18 else 'false',
            'link_flair_text': p.link_flair_text,
            'is_ai': bool(p.is_ai),
        }
        for p in posts
    ]

    # Interleave AI posts up to the requested ratio
    desired_ai = max(0, min(len(posts), int(round(len(posts) * AI_POSTS_RATIO))))
    ai_posts = get_ai_posts()[:desired_ai]
    for ai in ai_posts:
        idx = random.randint(0, len(resp_posts))
        resp_posts.insert(idx, ai)

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


