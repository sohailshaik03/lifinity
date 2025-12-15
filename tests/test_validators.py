"""Unit tests for validators module.

Run with: pytest tests/test_validators.py -v
"""
import pytest
from Retailsights.utils.validators import (
    Validators,
    ValidationError,
    require_valid_email,
    require_valid_password
)


class TestEmailValidation:
    """Test email validation functionality."""
    
    def test_valid_emails(self):
        """Test that valid emails pass validation."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "admin+test@subdomain.example.org",
            "123@numbers.com"
        ]
        for email in valid_emails:
            is_valid, error = Validators.validate_email(email)
            assert is_valid, f"'{email}' should be valid but got error: {error}"
            assert error is None
    
    def test_invalid_emails(self):
        """Test that invalid emails fail validation."""
        invalid_emails = [
            "",
            "not-an-email",
            "@example.com",
            "user@",
            "user @example.com",
            "a" * 256 + "@example.com"  # Too long
        ]
        for email in invalid_emails:
            is_valid, error = Validators.validate_email(email)
            assert not is_valid, f"'{email}' should be invalid"
            assert error is not None
    
    def test_require_valid_email(self):
        """Test require_valid_email raises on invalid input."""
        with pytest.raises(ValidationError):
            require_valid_email("invalid-email")
        
        # Should not raise
        result = require_valid_email("Valid@Example.COM")
        assert result == "valid@example.com"  # Should be lowercased


class TestPasswordValidation:
    """Test password validation functionality."""
    
    def test_valid_passwords(self):
        """Test that strong passwords pass validation."""
        valid_passwords = [
            "Password123",
            "MySecure1Pass",
            "Admin@123",
            "Str0ngP@ssw0rd!"
        ]
        for password in valid_passwords:
            is_valid, error = Validators.validate_password(password)
            assert is_valid, f"'{password}' should be valid but got error: {error}"
    
    def test_weak_passwords(self):
        """Test that weak passwords fail validation."""
        weak_passwords = [
            "short1A",           # Too short
            "alllowercase123",  # No uppercase
            "ALLUPPERCASE123",  # No lowercase
            "NoNumbers",        # No numbers
            ""                  # Empty
        ]
        for password in weak_passwords:
            is_valid, error = Validators.validate_password(password)
            assert not is_valid, f"'{password}' should be invalid"
            assert error is not None
    
    def test_custom_min_length(self):
        """Test password validation with custom minimum length."""
        is_valid, error = Validators.validate_password("Short1A", min_length=10)
        assert not is_valid
        assert "at least 10" in error


class TestFileValidation:
    """Test file upload validation."""
    
    def test_valid_data_files(self):
        """Test that valid data files pass validation."""
        valid_files = [
            ("data.csv", 1024 * 1024, "data"),
            ("report.xlsx", 5 * 1024 * 1024, "data"),
            ("export.json", 100 * 1024, "data")
        ]
        for filename, size, file_type in valid_files:
            is_valid, error = Validators.validate_file_upload(filename, size, file_type)
            assert is_valid, f"{filename} should be valid but got: {error}"
    
    def test_invalid_file_extension(self):
        """Test that invalid file extensions fail validation."""
        is_valid, error = Validators.validate_file_upload("malware.exe", 1024, "data")
        assert not is_valid
        assert "not allowed" in error.lower()
    
    def test_file_too_large(self):
        """Test that oversized files fail validation."""
        is_valid, error = Validators.validate_file_upload(
            "huge.csv",
            100 * 1024 * 1024,  # 100 MB
            "data"
        )
        assert not is_valid
        assert "too large" in error.lower()
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        malicious_files = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config",
            "file/../../../secret.txt"
        ]
        for filename in malicious_files:
            is_valid, error = Validators.validate_file_upload(filename, 1024, "data")
            assert not is_valid
            assert "path traversal" in error.lower()


class TestSanitization:
    """Test input sanitization functions."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert Validators.sanitize_filename("normal_file.csv") == "normal_file.csv"
        assert Validators.sanitize_filename("file with spaces.txt") == "file with spaces.txt"
        
        # Should remove dangerous characters
        dangerous = Validators.sanitize_filename("file<>:|?.txt")
        assert "<" not in dangerous
        assert ">" not in dangerous
        assert "|" not in dangerous
    
    def test_sanitize_sql_input(self):
        """Test SQL input sanitization."""
        # Should remove SQL comments
        assert "--" not in Validators.sanitize_sql_input("test -- comment")
        assert "/*" not in Validators.sanitize_sql_input("test /* comment */")
        
        # Should remove dangerous keywords
        dangerous = "DROP TABLE users"
        sanitized = Validators.sanitize_sql_input(dangerous)
        assert "DROP" not in sanitized.upper()


class TestBusinessValidation:
    """Test business logic validators."""
    
    def test_validate_shop_name(self):
        """Test shop name validation."""
        # Valid names
        is_valid, _ = Validators.validate_shop_name("Main Street Store")
        assert is_valid
        
        # Invalid names
        is_valid, error = Validators.validate_shop_name("")
        assert not is_valid
        
        is_valid, error = Validators.validate_shop_name("a")
        assert not is_valid
        
        is_valid, error = Validators.validate_shop_name("a" * 300)
        assert not is_valid
    
    def test_validate_product_sku(self):
        """Test SKU validation."""
        # Valid SKUs
        valid_skus = ["ABC123", "PROD-001", "item_42"]
        for sku in valid_skus:
            is_valid, error = Validators.validate_product_sku(sku)
            assert is_valid, f"SKU '{sku}' should be valid"
        
        # Invalid SKUs
        is_valid, _ = Validators.validate_product_sku("SKU WITH SPACES")
        assert not is_valid
        
        is_valid, _ = Validators.validate_product_sku("SKU@123")
        assert not is_valid
    
    def test_validate_price(self):
        """Test price validation."""
        # Valid prices
        assert Validators.validate_price(0.0)[0]
        assert Validators.validate_price(99.99)[0]
        assert Validators.validate_price(1000.50)[0]
        
        # Invalid prices
        assert not Validators.validate_price(-1.0)[0]
        assert not Validators.validate_price(9999999.99)[0]
        assert not Validators.validate_price(None)[0]
    
    def test_validate_quantity(self):
        """Test quantity validation."""
        # Valid quantities
        assert Validators.validate_quantity(0)[0]
        assert Validators.validate_quantity(1)[0]
        assert Validators.validate_quantity(100.5)[0]
        
        # Invalid quantities
        assert not Validators.validate_quantity(-1)[0]
        assert not Validators.validate_quantity(9999999)[0]
        assert not Validators.validate_quantity(None)[0]
    
    def test_validate_user_role(self):
        """Test user role validation."""
        # Valid roles
        for role in ['admin', 'manager', 'user', 'viewer']:
            is_valid, error = Validators.validate_user_role(role)
            assert is_valid, f"Role '{role}' should be valid"
        
        # Invalid role
        is_valid, error = Validators.validate_user_role('superuser')
        assert not is_valid
        assert "Invalid role" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
