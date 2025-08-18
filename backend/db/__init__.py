from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from config import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required. Set it to your external database (e.g., postgresql+psycopg://user:pass@host:5432/slop)")

# External DB engine (e.g., PostgreSQL)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = scoped_session(
    sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
)

@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


