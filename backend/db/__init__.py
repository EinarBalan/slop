import os
import sqlite3
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker
from config import DB_FILE, DATABASE_URL

if DATABASE_URL:
    # External DB (e.g., PostgreSQL). Example URL: postgresql+psycopg://user:pass@host:5432/slop
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
else:
    # SQLite local file
    engine = create_engine(
        f"sqlite:///{DB_FILE}",
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
    )

# Ensure SQLite pragmas are set for concurrency and performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Only applies to SQLite
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

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


