import csv
import os
import random
from sqlalchemy import select
from config import DATABASE_URL
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
    # CSV import is disabled when using external DB-only mode; implement your own ETL if needed
    print("CSV import skipped (external DB mode). Use a custom ETL to load posts.")
    return 0


def seed_if_empty():
    init_db()
    with db_session() as session:
        count = session.query(Post).count()
        print(f"DB has {count} posts; no automatic seeding in external DB mode")


def clear_served_posts():
    """Clear per-user served history so posts can be reshown between server sessions."""
    with db_session() as session:
        deleted = session.query(ServedPost).delete()
        print(f"Cleared {deleted} entries from served_posts")


if __name__ == '__main__':
    seed_if_empty()


