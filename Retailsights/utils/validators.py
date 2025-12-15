"""Input validation utilities for security and data integrity.

Provides comprehensive validation for user inputs, file uploads, and data processing
to prevent security vulnerabilities and ensure data quality.
"""
import re
from typing import Optional, Tuple
from pathlib import Path


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class Validators:
    """Collection of input validation methods."""
    
    # Email regex pattern (RFC 5322 simplified)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Allowed file extensions for uploads
    ALLOWED_EXTENSIONS = {
        'data': {'.csv', '.xlsx', '.xls', '.json'},
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp'},
        'document': {'.pdf', '.doc', '.docx', '.txt'}
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = {
        'data': 50 * 1024 * 1024,      # 50 MB
        'image': 10 * 1024 * 1024,     # 10 MB
        'document': 20 * 1024 * 1024,  # 20 MB
    }
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            >>> is_valid, error = Validators.validate_email("user@example.com")
            >>> if not is_valid:
            ...     print(error)
        """
        if not email:
            return False, "Email is required"
        
        if len(email) > 255:
            return False, "Email is too long (max 255 characters)"
        
        if not Validators.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        return True, None
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
        """Validate password strength.
        
        Args:
            password: Password to validate
            min_length: Minimum required length (default: 8)
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Requirements:
            - Minimum length (default 8 characters)
            - At least one uppercase letter
            - At least one lowercase letter
            - At least one number
        """
        if not password:
            return False, "Password is required"
        
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, None
    
    @staticmethod
    def validate_file_upload(
        filename: str,
        file_size: int,
        file_type: str = 'data'
    ) -> Tuple[bool, Optional[str]]:
        """Validate file upload for security and size constraints.
        
        Args:
            filename: Name of uploaded file
            file_size: Size of file in bytes
            file_type: Type of file ('data', 'image', 'document')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "Filename is required"
        
        # Check file extension
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        allowed = Validators.ALLOWED_EXTENSIONS.get(file_type, set())
        if extension not in allowed:
            return False, f"File type '{extension}' not allowed. Allowed: {', '.join(allowed)}"
        
        # Check file size
        max_size = Validators.MAX_FILE_SIZE.get(file_type, 10 * 1024 * 1024)
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb:.1f}MB"
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Invalid filename: path traversal detected"
        
        return True, None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove path components
        filename = Path(filename).name
        
        # Replace dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            stem = filename[:200]
            extension = Path(filename).suffix
            filename = stem + extension
        
        return filename
    
    @staticmethod
    def validate_shop_name(name: str) -> Tuple[bool, Optional[str]]:
        """Validate shop name.
        
        Args:
            name: Shop name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Shop name is required"
        
        if len(name) < 2:
            return False, "Shop name must be at least 2 characters"
        
        if len(name) > 255:
            return False, "Shop name is too long (max 255 characters)"
        
        # Check for SQL injection patterns
        dangerous_patterns = ['--', ';--', '/*', '*/', 'xp_', 'sp_', 'exec', 'execute']
        name_lower = name.lower()
        if any(pattern in name_lower for pattern in dangerous_patterns):
            return False, "Shop name contains invalid characters"
        
        return True, None
    
    @staticmethod
    def validate_product_sku(sku: str) -> Tuple[bool, Optional[str]]:
        """Validate product SKU format.
        
        Args:
            sku: SKU to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sku or not sku.strip():
            return False, "SKU is required"
        
        if len(sku) > 100:
            return False, "SKU is too long (max 100 characters)"
        
        # SKU should be alphanumeric with hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', sku):
            return False, "SKU can only contain letters, numbers, hyphens, and underscores"
        
        return True, None
    
    @staticmethod
    def validate_price(price: float) -> Tuple[bool, Optional[str]]:
        """Validate price value.
        
        Args:
            price: Price to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if price is None:
            return False, "Price is required"
        
        if price < 0:
            return False, "Price cannot be negative"
        
        if price > 999999.99:
            return False, "Price is too high (max 999,999.99)"
        
        return True, None
    
    @staticmethod
    def validate_quantity(quantity: float) -> Tuple[bool, Optional[str]]:
        """Validate quantity value.
        
        Args:
            quantity: Quantity to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if quantity is None:
            return False, "Quantity is required"
        
        if quantity < 0:
            return False, "Quantity cannot be negative"
        
        if quantity > 999999:
            return False, "Quantity is too high (max 999,999)"
        
        return True, None
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """Sanitize user input to prevent SQL injection.
        
        Note: This is a defense-in-depth measure. Always use parameterized
        queries as the primary defense against SQL injection.
        
        Args:
            value: Input value to sanitize
            
        Returns:
            Sanitized value
        """
        if not isinstance(value, str):
            return value
        
        # Remove SQL comment indicators
        value = value.replace('--', '')
        value = value.replace('/*', '')
        value = value.replace('*/', '')
        
        # Remove common SQL injection patterns
        dangerous_keywords = [
            'DROP', 'DELETE', 'TRUNCATE', 'EXEC', 'EXECUTE',
            'xp_', 'sp_', 'UNION', 'INSERT', 'UPDATE'
        ]
        
        for keyword in dangerous_keywords:
            value = re.sub(f'\\b{keyword}\\b', '', value, flags=re.IGNORECASE)
        
        return value.strip()
    
    @staticmethod
    def validate_user_role(role: str) -> Tuple[bool, Optional[str]]:
        """Validate user role.
        
        Args:
            role: Role to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_roles = {'admin', 'manager', 'user', 'viewer'}
        
        if not role:
            return False, "Role is required"
        
        if role.lower() not in valid_roles:
            return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        
        return True, None


# Convenience functions for common validations
def require_valid_email(email: str) -> str:
    """Validate email or raise ValidationError.
    
    Args:
        email: Email to validate
        
    Returns:
        Validated email
        
    Raises:
        ValidationError: If email is invalid
    """
    is_valid, error = Validators.validate_email(email)
    if not is_valid:
        raise ValidationError(error)
    return email.lower().strip()


def require_valid_password(password: str, min_length: int = 8) -> str:
    """Validate password or raise ValidationError.
    
    Args:
        password: Password to validate
        min_length: Minimum required length
        
    Returns:
        Validated password
        
    Raises:
        ValidationError: If password is invalid
    """
    is_valid, error = Validators.validate_password(password, min_length)
    if not is_valid:
        raise ValidationError(error)
    return password
