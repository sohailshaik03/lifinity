"""
Input validation and sanitization
Prevent injection attacks and ensure data integrity
"""
import re
from typing import Any, Dict, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    errors: List[str]
    sanitized_value: Any = None


class Validator:
    """Input validation utilities"""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?1?\d{9,15}$')
    SQL_INJECTION_PATTERN = re.compile(r"(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bUNION\b|--|;|\/\*|\*\/)", re.IGNORECASE)
    XSS_PATTERN = re.compile(r'<script|javascript:|onerror=|onload=', re.IGNORECASE)
    
    @classmethod
    def validate_email(cls, email: str) -> ValidationResult:
        """Validate email format"""
        errors = []
        
        if not email:
            errors.append("Email is required")
            return ValidationResult(False, errors)
        
        email = email.strip().lower()
        
        if not cls.EMAIL_PATTERN.match(email):
            errors.append("Invalid email format")
        
        if len(email) > 255:
            errors.append("Email too long (max 255 characters)")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_value=email
        )
    
    @classmethod
    def validate_password(cls, password: str, min_length: int = 8, require_special: bool = True) -> ValidationResult:
        """Validate password strength"""
        errors = []
        
        if not password:
            errors.append("Password is required")
            return ValidationResult(False, errors)
        
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_value=password
        )
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> ValidationResult:
        """Sanitize string input to prevent XSS and SQL injection"""
        errors = []
        
        if not value:
            return ValidationResult(True, [], "")
        
        # Check for SQL injection patterns
        if cls.SQL_INJECTION_PATTERN.search(value):
            errors.append("Input contains potentially malicious SQL patterns")
        
        # Check for XSS patterns
        if cls.XSS_PATTERN.search(value):
            errors.append("Input contains potentially malicious script patterns")
        
        # Truncate if too long
        sanitized = value[:max_length]
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_value=sanitized
        )
    
    @classmethod
    def validate_integer(cls, value: Any, min_val: int = None, max_val: int = None) -> ValidationResult:
        """Validate integer input"""
        errors = []
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            errors.append("Value must be a valid integer")
            return ValidationResult(False, errors)
        
        if min_val is not None and int_value < min_val:
            errors.append(f"Value must be at least {min_val}")
        
        if max_val is not None and int_value > max_val:
            errors.append(f"Value must be at most {max_val}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_value=int_value
        )
    
    @classmethod
    def validate_float(cls, value: Any, min_val: float = None, max_val: float = None) -> ValidationResult:
        """Validate float input"""
        errors = []
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            errors.append("Value must be a valid number")
            return ValidationResult(False, errors)
        
        if min_val is not None and float_value < min_val:
            errors.append(f"Value must be at least {min_val}")
        
        if max_val is not None and float_value > max_val:
            errors.append(f"Value must be at most {max_val}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_value=float_value
        )
    
    @classmethod
    def validate_phone(cls, phone: str) -> ValidationResult:
        """Validate phone number"""
        errors = []
        
        if not phone:
            return ValidationResult(True, [], None)
        
        # Remove common formatting characters
        sanitized = re.sub(r'[\s\-\(\)]', '', phone)
        
        if not cls.PHONE_PATTERN.match(sanitized):
            errors.append("Invalid phone number format")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_value=sanitized if len(errors) == 0 else None
        )


def validate_user_registration(data: Dict[str, Any]) -> ValidationResult:
    """Validate user registration data"""
    errors = []
    sanitized = {}
    
    # Validate email
    email_result = Validator.validate_email(data.get('email', ''))
    if not email_result.is_valid:
        errors.extend(email_result.errors)
    else:
        sanitized['email'] = email_result.sanitized_value
    
    # Validate password
    password_result = Validator.validate_password(data.get('password', ''))
    if not password_result.is_valid:
        errors.extend(password_result.errors)
    else:
        sanitized['password'] = password_result.sanitized_value
    
    # Validate full name
    name_result = Validator.sanitize_string(data.get('full_name', ''), max_length=255)
    if not name_result.is_valid:
        errors.extend(name_result.errors)
    elif not name_result.sanitized_value:
        errors.append("Full name is required")
    else:
        sanitized['full_name'] = name_result.sanitized_value
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        sanitized_value=sanitized if len(errors) == 0 else None
    )
