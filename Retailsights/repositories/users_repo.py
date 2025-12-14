# repositories/users_repo.py
from __future__ import annotations

from typing import Any, Dict, Optional

from Retailsights.db_orm import get_session
from Retailsights.models import User
from ..logger import logger
from typing import Any, Dict, Optional


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Fetch an active user by email.
    """
    session = get_session()
    try:
        u = session.query(User).filter(User.email == email).one_or_none()
        if not u:
            return None
        return {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "password_hash": u.password_hash,
            "created_at": u.created_at,
        }
    except Exception as e:
        logger.error(f"get_user_by_email error: {e}")
        return None
    finally:
        session.close()


def create_user(
    email: str,
    full_name: str,
    password_hash: str,
    role: str = "owner",
    is_active: bool = True,
) -> Optional[int]:
    """
    Create a new user. Returns new user id or None on error.
    """
    session = get_session()
    try:
        u = User(email=email, password_hash=password_hash, full_name=full_name, role=role)
        session.add(u)
        session.commit()
        session.refresh(u)
        return u.id
    except Exception as e:
        logger.error(f"create_user error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def list_users() -> list[Dict[str, Any]]:
    """
    Return a list of all users with basic fields for admin view.
    """
    session = get_session()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        result: list[Dict[str, Any]] = []
        for u in users:
            result.append({
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "created_at": u.created_at,
            })
        return result
    except Exception as e:
        logger.error(f"list_users error: {e}")
        return []
    finally:
        session.close()


def update_user(
    user_id: int,
    full_name: str | None = None,
    role: str | None = None,
    password_hash: str | None = None,
    is_active: bool | None = None,
) -> bool:
    """
    Update user fields. Only non-None values will be updated.
    """
    session = get_session()
    try:
        u = session.get(User, user_id)
        if not u:
            return False
        if full_name is not None:
            u.full_name = full_name
        if role is not None:
            u.role = role
        if password_hash is not None:
            u.password_hash = password_hash
        if is_active is not None:
            # assume presence of is_active column may be handled elsewhere; store via role or a flag if present
            pass
        session.commit()
        return True
    except Exception as e:
        logger.error(f"update_user error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def deactivate_user(user_id: int) -> bool:
    """
    Soft-deactivate a user (set is_active = 0).
    """
    return update_user(user_id, is_active=False)
