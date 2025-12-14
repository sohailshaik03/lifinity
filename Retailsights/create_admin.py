# create_admin.py
from __future__ import annotations
import getpass
import sys
import bcrypt

# Handle imports for both module and script execution
if __name__ == "__main__":
    # When run as script, add parent directory to path
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .db import get_session
from .logger import logger
from .models import User
from utils.validation import validate_email

def prompt_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Value cannot be empty.\n")

def create_admin_user() -> None:
    print("=== RetailSight admin user creation ===")
    
    # Email with validation
    while True:
        email = input("Admin email: ").strip()
        if not email:
            print("❌ Email cannot be empty.\n")
            continue
        if not validate_email(email):
            print("❌ Invalid email format. Please try again.\n")
            continue
        break
    
    full_name = prompt_non_empty("Full name: ")
    
    # Password (twice, hidden)
    while True:
        password = getpass.getpass("Password: 7330956544@shaik")
        password2 = getpass.getpass("Confirm password: 7330956544@shaik")
        
        if not password:
            print("❌ Password cannot be empty.\n")
            continue
        if password != password2:
            print("❌ Passwords do not match. Try again.\n")
            continue
        if len(password) < 8:
            print("❌ Password must be at least 8 characters.\n")
            continue
        break
    
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    
    # Insert into DB
    try:
        session = get_session()

        # Check if user already exists
        existing = session.query(User).filter(User.email == email).one_or_none()
        if existing:
            print(f"⚠️  User with email {email} already exists (id={existing.id}).")
            session.close()
            return

        user = User(email=email, password_hash=password_hash, full_name=full_name, role='admin')
        session.add(user)
        session.commit()
        session.refresh(user)

        print("✅ Admin user created successfully.")

    except Exception as e:
        print("❌ Failed to create admin user:", e)
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    create_admin_user()
    
    
    
    
    
    