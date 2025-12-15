#!/usr/bin/env python3
"""Create admin user with specific credentials"""
import sys
import os
import bcrypt

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_session
from models import User

def create_admin():
    email = "admin@gmail.com"
    password = "Admin@123"
    full_name = "Admin"
    
    # Hash password
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    
    try:
        session = get_session()
        
        # Check if user already exists
        existing = session.query(User).filter(User.email == email).one_or_none()
        if existing:
            print(f"⚠️  User {email} already exists. Updating password...")
            existing.password_hash = password_hash
            existing.full_name = full_name
            existing.role = 'admin'
            existing.is_active = True
            session.commit()
            print(f"✅ Admin user updated: {email}")
        else:
            # Create new admin user
            user = User(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                role='admin',
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"✅ Admin user created: {email} (ID: {user.id})")
        
        print(f"\nLogin credentials:")
        print(f"Email: {email}")
        print(f"Password: {password}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    create_admin()
