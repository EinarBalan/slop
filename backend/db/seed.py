import csv
import os
import random
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from config import DATABASE_URL
from db import engine, db_session
from db.models import Base, Post, ServedPost, Experiment


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


# def _find_posts_csv() -> Path | None:
#     # Try common locations
#     candidates = [
#         Path(__file__).resolve().parent.parent / 'data' / 'posts.csv',          # backend/data/posts.csv
#         Path(__file__).resolve().parent.parent / 'posts.csv',                   # backend/posts.csv
#         Path(__file__).resolve().parents[2] / 'data' / 'posts.csv',            # repo_root/data/posts.csv
#     ]
#     for p in candidates:
#         if p.exists():
#             return p
#     return None


def load_posts_from_csv(limit: int | None = None, batch_size: int = 1000) -> int:
    csv_path = './data/posts.csv' #_find_posts_csv()
    if not csv_path:
        print("No posts.csv found. Skipping seed.")
        return 0

    print(f"Seeding posts from {csv_path}")
    inserted = 0
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        batch: list[Post] = []
        with db_session() as session:
            for row in reader:
                if limit is not None and inserted >= limit:
                    break
                if not is_valid_row(row):
                    continue
                try:
                    post = Post(
                        post_id=row.get('post_id') or row.get('id') or None,
                        title=row.get('title', '')[:10000],
                        self_text=row.get('self_text', '')[:100000],
                        subreddit=row.get('subreddit'),
                        over_18=str(row.get('over_18', 'false')).lower() == 'true',
                        link_flair_text=row.get('link_flair_text'),
                        is_ai=False,
                        random_key=random.getrandbits(63),
                    )
                    session.add(post)
                    session.flush()  # catch duplicates early (unique post_id)
                    inserted += 1
                except IntegrityError:
                    session.rollback()
                    # Duplicate post_id (or other constraint) — skip
                    continue

                if inserted % batch_size == 0:
                    print(f"Inserted {inserted} posts...")

    print(f"Finished seeding. Inserted {inserted} posts.")
    return inserted


def seed_if_empty():
    init_db()
    with db_session() as session:
        count = session.query(Post).count()
        if count == 0:
            # Attempt to seed from CSV
            try:
                added = load_posts_from_csv()
                print(f"Seeded {added} posts from CSV.")
            except Exception as e:
                print(f"Automatic CSV seed failed: {e}")
        else:
            print(f"DB has {count} posts; skipping seed")


def clear_served_posts():
    """Clear per-user served history so posts can be reshown between server sessions."""
    with db_session() as session:
        deleted = session.query(ServedPost).delete()
        print(f"Cleared {deleted} entries from served_posts")


if __name__ == '__main__':
    seed_if_empty()


