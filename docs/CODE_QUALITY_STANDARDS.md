# Code Quality Standards

## Overview
This document defines the coding standards and best practices for the RetailSights application. Following these standards ensures maintainable, secure, and performant code.

## Table of Contents
1. [Python Code Style](#python-code-style)
2. [Type Hints](#type-hints)
3. [Documentation](#documentation)
4. [Error Handling](#error-handling)
5. [Security](#security)
6. [Testing](#testing)
7. [Performance](#performance)
8. [Git Workflow](#git-workflow)

---

## Python Code Style

### PEP 8 Compliance
All Python code must follow [PEP 8](https://pep8.org/) style guidelines.

**Formatting Tools:**
```bash
# Format code with black
black Retailsights/

# Sort imports with isort
isort Retailsights/

# Check style with flake8
flake8 Retailsights/ --max-line-length=100
```

### Code Organization
```python
# 1. Module docstring
"""Module description here."""

# 2. Imports (grouped and sorted)
from __future__ import annotations  # For forward references

import os
import sys
from typing import Optional, List

import pandas as pd
import streamlit as st

from Retailsights.config import config
from Retailsights.logger import log

# 3. Constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# 4. Classes and functions
class MyClass:
    """Class docstring."""
    pass
```

### Naming Conventions
- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `lowercase_with_underscores()`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`
- **Private**: `_leading_underscore`

---

## Type Hints

### Required Type Hints
All public functions and methods must have type hints for parameters and return values.

**Example:**
```python
from typing import Optional, List, Dict, Tuple

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch user by email address.
    
    Args:
        email: User's email address
        
    Returns:
        User dictionary or None if not found
    """
    ...

def calculate_discount(
    price: float,
    discount_percent: float
) -> Tuple[float, float]:
    """Calculate discounted price.
    
    Args:
        price: Original price
        discount_percent: Discount percentage (0-100)
        
    Returns:
        Tuple of (discounted_price, savings)
    """
    savings = price * (discount_percent / 100)
    return price - savings, savings
```

### Type Checking
Run mypy for static type checking:
```bash
mypy Retailsights/ --ignore-missing-imports
```

---

## Documentation

### Module Docstrings
Every module must have a docstring explaining its purpose.

```python
"""User authentication and session management.

This module handles user login, logout, password hashing, and session
persistence across page refreshes. Uses bcrypt for secure password hashing.
"""
```

### Function/Method Docstrings
Use Google-style docstrings for all public functions:

```python
def create_user(
    email: str,
    password: str,
    full_name: str,
    role: str = "user"
) -> Dict[str, Any]:
    """Create a new user account.
    
    Args:
        email: User's email address (must be unique)
        password: Plain text password (will be hashed)
        full_name: User's full name
        role: User role (default: "user")
        
    Returns:
        Dictionary containing user data with keys: id, email, full_name, role
        
    Raises:
        ValidationError: If email is invalid or password too weak
        IntegrityError: If email already exists
        
    Example:
        >>> user = create_user("admin@shop.com", "SecurePass1", "Admin User", "admin")
        >>> print(user['email'])
        admin@shop.com
    """
    ...
```

### Class Docstrings
```python
class CacheManager:
    """Manage application-wide caching with Redis/Upstash fallback.
    
    Implements three-tier caching strategy:
    1. Upstash REST API (serverless)
    2. Standard Redis (self-hosted)
    3. Streamlit cache (fallback)
    
    Attributes:
        TTL_SHORT: 60 seconds for frequently changing data
        TTL_MEDIUM: 300 seconds for semi-static data
        TTL_LONG: 3600 seconds for static data
        
    Example:
        >>> cache = CacheManager()
        >>> cache.set("user:123", user_data, ttl=300)
        >>> cached = cache.get("user:123")
    """
```

---

## Error Handling

### Specific Exceptions
**Never use bare `except:`** - Always catch specific exceptions.

❌ **Bad:**
```python
try:
    result = dangerous_operation()
except:
    pass
```

✅ **Good:**
```python
try:
    result = dangerous_operation()
except (ValueError, TypeError) as e:
    logger.error(f"Operation failed: {e}")
    return None
```

### Custom Exceptions
Define custom exceptions for domain-specific errors:

```python
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class InsufficientInventoryError(Exception):
    """Raised when product stock is insufficient."""
    pass
```

### Error Logging
Always log errors with context:

```python
from loguru import logger

try:
    user = get_user_by_id(user_id)
except DatabaseError as e:
    logger.exception(f"Failed to fetch user {user_id}: {e}")
    raise
```

---

## Security

### Input Validation
**Always validate user input** before processing.

```python
from Retailsights.utils.validators import Validators, ValidationError

def create_shop(name: str) -> dict:
    """Create a new shop."""
    # Validate input
    is_valid, error = Validators.validate_shop_name(name)
    if not is_valid:
        raise ValidationError(error)
    
    # Proceed with creation
    ...
```

### SQL Injection Prevention
**Always use parameterized queries** - never concatenate SQL strings.

❌ **Bad:**
```python
query = f"SELECT * FROM users WHERE email = '{email}'"
result = conn.execute(query)
```

✅ **Good:**
```python
from sqlalchemy import text

query = text("SELECT * FROM users WHERE email = :email")
result = conn.execute(query, {"email": email})
```

### Password Security
- Always hash passwords with bcrypt
- Never log or display passwords
- Enforce minimum password strength

```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())
```

### Environment Variables
**Never hardcode secrets** - use environment variables.

❌ **Bad:**
```python
DB_PASSWORD = "Shybash630shaik@"
OPENAI_API_KEY = "sk-abc123xyz"
```

✅ **Good:**
```python
import os
DB_PASSWORD = os.getenv("DB_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

---

## Testing

### Test Structure
Organize tests to mirror source code structure:

```
Retailsights/
  utils/
    validators.py
    cache_manager.py
tests/
  test_validators.py
  test_cache_manager.py
```

### Writing Tests
Use pytest with clear test names:

```python
import pytest
from Retailsights.utils.validators import Validators

class TestEmailValidation:
    """Test email validation functionality."""
    
    def test_valid_emails_pass_validation(self):
        """Test that correctly formatted emails pass."""
        valid_emails = ["user@example.com", "admin@shop.co.uk"]
        for email in valid_emails:
            is_valid, error = Validators.validate_email(email)
            assert is_valid
            assert error is None
    
    def test_invalid_emails_fail_validation(self):
        """Test that malformed emails fail."""
        is_valid, error = Validators.validate_email("not-an-email")
        assert not is_valid
        assert error is not None
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=Retailsights --cov-report=html

# Run specific test file
pytest tests/test_validators.py -v
```

### Test Coverage Goals
- Aim for **>80% code coverage**
- **100% coverage** for critical paths (auth, payments, data integrity)

---

## Performance

### Database Queries
- Use indexing on frequently queried columns
- Implement pagination for large datasets
- Cache expensive queries

```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_user_by_email(email: str) -> Optional[dict]:
    """Fetch user by email (cached)."""
    ...
```

### Caching Strategy
```python
from Retailsights.utils.cache_manager import CacheManager

cache = CacheManager()

# Short TTL for dynamic data
cache.set("active_users", data, ttl=CacheManager.TTL_SHORT)

# Long TTL for static data
cache.set("product_categories", data, ttl=CacheManager.TTL_LONG)
```

### Lazy Loading
Load data only when needed:

```python
# Bad: Load all products upfront
products = get_all_products()  # Could be millions

# Good: Load paginated
products = get_products_page(page=1, size=50)
```

---

## Git Workflow

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add user role validation
fix: Prevent SQL injection in shop search
docs: Update API documentation
refactor: Simplify cache manager initialization
test: Add tests for password validation
perf: Optimize product query with indexing
```

### Branch Naming
```
feature/user-authentication
bugfix/session-persistence
hotfix/security-vulnerability
refactor/cache-layer
```

### Pull Request Checklist
Before submitting a PR:
- [ ] All tests pass (`pytest tests/`)
- [ ] Code is formatted (`black`, `isort`)
- [ ] No linting errors (`flake8`)
- [ ] Type checking passes (`mypy`)
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered

---

## Pre-commit Hooks

Install pre-commit hooks to enforce standards:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**`.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']
```

---

## Code Review Guidelines

### For Reviewers
- Check for security vulnerabilities
- Verify test coverage
- Ensure documentation is clear
- Look for performance issues
- Validate error handling

### For Authors
- Keep PRs focused and small
- Provide context in description
- Link related issues
- Respond to feedback promptly
- Update based on comments

---

## Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [SQLAlchemy Best Practices](https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [Streamlit Performance](https://docs.streamlit.io/library/advanced-features/caching)

---

## Questions?

For questions about code standards, reach out to the team lead or open a discussion in GitHub Issues.
