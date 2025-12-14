# utils/validation.py
from __future__ import annotations

import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    """
    if not email:
        return False
    return EMAIL_REGEX.match(email) is not None
