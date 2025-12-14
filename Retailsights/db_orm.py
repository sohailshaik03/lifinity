import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # prefer explicit DATABASE_URL for production; fall back to sqlite for local testing
    DATABASE_URL = os.getenv("DB_URL_SQLITE") or f"sqlite:///retailsight_dev.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

def get_session():
    return SessionLocal()


def create_all_tables(base):
    base.metadata.create_all(bind=engine)
