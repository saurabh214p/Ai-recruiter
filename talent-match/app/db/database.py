"""
Database setup using SQLAlchemy.

Reads DATABASE_URL from the environment so this can point at a hosted
Postgres instance (Render, Supabase, etc.) — the same pattern as your
Spring Boot API. Falls back to a local SQLite file if DATABASE_URL is
not set, so the app still runs out of the box with zero config.

Example DATABASE_URL values:
    Supabase:  postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
    Render:    postgresql://user:password@host:5432/dbname
    Local:     postgresql://postgres:postgres@localhost:5432/talent_match

Set it before running the app:
    export DATABASE_URL="postgresql://..."   (Mac/Linux)
    setx DATABASE_URL "postgresql://..."     (Windows)
"""
import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./talent_match.db")

# Supabase/Render sometimes hand out "postgres://" URLs — SQLAlchemy's
# psycopg driver wants the "postgresql://" scheme.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    logger.warning(
        "DATABASE_URL is not set — falling back to local SQLite (talent_match.db). "
        "Set DATABASE_URL to your hosted Postgres connection string for production-style use."
    )
    # check_same_thread=False is needed because FastAPI can use the
    # same SQLite connection across different threads in a single request lifecycle.
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    logger.info("Connecting to Postgres database.")
    # pool_pre_ping avoids "server closed the connection" errors against
    # hosted Postgres instances that close idle connections after a timeout.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
