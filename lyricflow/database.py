"""
Database setup for LyricFlow.

Why SQLite + SQLAlchemy?
- SQLite needs zero setup (single file), perfect for a local-first PWA.
- SQLAlchemy gives us Python classes instead of raw SQL strings,
  so the code reads like "get me Song #5" instead of writing queries by hand.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env so DATABASE_URL (and other vars) are available.
# Must happen here because database.py is imported early by main.py.
load_dotenv()

# "check_same_thread=False" is required for SQLite + FastAPI because
# FastAPI handles requests across multiple threads, but SQLite's default
# mode only allows the thread that created the connection to use it.
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///./lyricflow.db"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# autocommit=False: we control when data is saved (explicit > implicit)
# autoflush=False: prevents surprise writes mid-query
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Every model class will inherit from Base — it's the "registry"
# that tracks all our tables so create_all() knows what to build.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.

    Think of it like checking out a library book:
    - yield gives you the session (check out)
    - finally closes it (return the book) even if something crashes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
