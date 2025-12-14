"""
Database migration: Add is_active column to users table
Run this once to update existing database schema
"""
from sqlalchemy import text
from db import engine
from logger import log


def migrate_add_is_active():
    """Add is_active column to users table"""
    
    migrations = [
        # Add is_active column with default True
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL;
        """,
        
        # Update existing users to be active
        """
        UPDATE users 
        SET is_active = TRUE 
        WHERE is_active IS NULL;
        """
    ]
    
    try:
        with engine.connect() as conn:
            for migration in migrations:
                log.info(f"Running migration: {migration.strip()[:50]}...")
                conn.execute(text(migration))
                conn.commit()
        
        log.info("✅ Migration completed: is_active column added")
        return True
    
    except Exception as e:
        log.error(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate_add_is_active()
    if success:
        print("✅ Database migration successful!")
    else:
        print("❌ Database migration failed!")
