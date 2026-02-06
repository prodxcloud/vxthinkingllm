"""
Database Connection and Session Management
Supports PostgreSQL with SQLAlchemy. Uses app.core.db (vacloudopsdb1) when DATABASE_URL is not set.
"""
import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger("vallm")


def _build_database_url() -> str:
    """Single source: use db.py config (database vacloudopsdb1) unless DATABASE_URL is set."""
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    try:
        try:
            from app.core.db import get_db_config
        except ImportError:
            from ...core.db import get_db_config
        cfg = get_db_config()
        user = quote_plus(cfg["user"])
        password = quote_plus(cfg["password"])
        return f"postgresql://{user}:{password}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    except Exception:
        pass
    return (
        f"postgresql://{quote_plus(os.getenv('POSTGRES_USER', 'postgres'))}:"
        f"{quote_plus(os.getenv('POSTGRES_PASSWORD', 'postgres'))}@"
        f"{os.getenv('POSTGRES_HOST', '127.0.0.1')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'vacloudopsdb1')}"
    )


# Database configuration (uses vacloudopsdb1 via db.py when DATABASE_URL unset)
DATABASE_URL = _build_database_url()

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session
    Usage: async def endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    Usage: with get_db_context() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
