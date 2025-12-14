# services/user_service.py
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from ..repositories.users_repo import create_user, get_user_by_email
from ..utils.security import hash_password, is_password_strong, verify_password
from ..utils.validation import validate_email


def authenticate_user(
    email: str, password: str
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Return (success, user_dict, message).
    """
    if not validate_email(email):
        return False, None, "Invalid email format."

    user = get_user_by_email(email)
    if not user:
        return False, None, "User not found."

    if not user.get("is_active"):
        return False, None, "User account is inactive."

    if not verify_password(password, user["password_hash"]):
        return False, None, "Incorrect password."

    # Strip sensitive fields
    safe_user = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
    }
    return True, safe_user, "Login successful."


def register_user(
    email: str, full_name: str, raw_password: str, role: str = "owner"
) -> Tuple[bool, Optional[int], str]:
    """
    Simple registration helper. (You might only use this for CLI/admin.)
    """
    if not validate_email(email):
        return False, None, "Invalid email format."

    if not is_password_strong(raw_password):
        return (
            False,
            None,
            "Password too weak. Use at least 8 chars with letters and numbers.",
        )

    pw_hash = hash_password(raw_password)
    user_id = create_user(
        email=email, full_name=full_name, password_hash=pw_hash, role=role
    )
    if user_id is None:
        return False, None, "Failed to create user (DB error)."

    return True, user_id, "User created."
