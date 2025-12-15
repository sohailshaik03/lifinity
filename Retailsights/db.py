# db.py
from __future__ import annotations

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Handle imports for both module and script execution
try:
    from .logger import logger
except ImportError:
    # Fallback for standalone execution
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# =============================
# ENV CONFIG
# =============================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set for PostgreSQL connection")

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

# =============================
# GLOBAL ENGINE AND SESSION
# =============================
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=DB_POOL_RECYCLE,  # Recycle connections after 1 hour
    pool_timeout=30,  # Wait max 30s for connection
    echo=False,
    future=True,
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30s query timeout
    }
)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


def init_db_pool():
    """Initialize PostgreSQL connection pool once."""
    try:
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL database pool initialised successfully.")
    except Exception as e:
        logger.exception("❌ Failed to initialise DB pool: %s", e)
        raise


def get_connection():
    """Return a fresh PostgreSQL connection from the pool."""
    try:
        conn = engine.connect()
        return conn
    except Exception as e:
        logger.exception("❌ Could not get connection from pool: %s", e)
        raise


def get_session():
    """Return a SQLAlchemy session."""
    return SessionLocal()


def health_check() -> bool:
    """Return True if DB connection works."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("❌ DB health check failed: %s", e)
        return False


def close_session():
    """Close the current session."""
    SessionLocal.remove()
