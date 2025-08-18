import csv
import os
import random
from sqlalchemy import select
from config import CSV_FILE
from db import engine, db_session
from db.models import Base, Post, ServedPost


def init_db():
    Base.metadata.create_all(bind=engine)


def is_valid_row(row):
    if not row.get('self_text'):
        return False
    text = row['self_text'].strip()
    if text == '' or text == '[deleted]' or text == '[removed]':
        return False
    if str(row.get('over_18', 'false')).lower() == 'true':
        return False
    return True


def load_posts_from_csv(limit=None):
    if not os.path.exists(CSV_FILE):
        print(f"CSV file not found: {CSV_FILE}")
        return 0

    inserted = 0
    with db_session() as session:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and inserted >= limit:
                    break
                if not is_valid_row(row):
                    continue
                try:
                    post = Post(
                        post_id=row.get('id') or row.get('post_id') or None,
                        title=row.get('title') or '',
                        self_text=row.get('self_text') or '',
                        subreddit=row.get('subreddit') or None,
                        over_18=str(row.get('over_18', 'false')).lower() == 'true',
                        link_flair_text=row.get('link_flair_text') or None,
                        is_ai=False,
                        random_key=random.getrandbits(63),
                    )
                    session.add(post)
                    inserted += 1
                except Exception:
                    session.rollback()
    return inserted


def seed_if_empty():
    init_db()
    with db_session() as session:
        count = session.query(Post).count()
        if count == 0:
            print("Seeding posts from CSV...")
            n = load_posts_from_csv()
            print(f"Seeded {n} posts from CSV")
        else:
            print(f"DB already has {count} posts; skipping seed")


def clear_served_posts():
    """Clear per-user served history so posts can be reshown between server sessions."""
    with db_session() as session:
        deleted = session.query(ServedPost).delete()
        print(f"Cleared {deleted} entries from served_posts")


if __name__ == '__main__':
    seed_if_empty()


