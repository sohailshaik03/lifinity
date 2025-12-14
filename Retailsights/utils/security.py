# utils/security.py
from __future__ import annotations

from typing import Optional

import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """
    if not plain_password:
        raise ValueError("Password cannot be empty")

    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    """
    if not plain_password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


def is_password_strong(password: str) -> bool:
    """
    Simple strength check (you can improve later):
    - At least 8 chars
    - Has digit
    - Has letter
    """
    if len(password) < 8:
        return False

    has_digit = any(ch.isdigit() for ch in password)
    has_letter = any(ch.isalpha() for ch in password)

    return has_digit and has_letter
