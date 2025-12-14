"""
Database initialization script for Streamlit Cloud deployment
This creates all required tables using SQLAlchemy models
"""
from models import Base
from db import engine
from logger import log

def init_database():
    """Create all database tables"""
    try:
        log.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        log.info("✅ All database tables created successfully!")
        return True
    except Exception as e:
        log.error(f"❌ Failed to create tables: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("✅ Database initialized successfully!")
    else:
        print("❌ Database initialization failed!")
