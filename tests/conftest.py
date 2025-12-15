"""Pytest configuration and fixtures for RetailSights tests."""
import os
import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["ENV"] = "test"
os.environ["DB_NAME"] = "retailsight_test"


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "env": "test",
        "db_name": "retailsight_test",
        "log_level": "DEBUG"
    }


@pytest.fixture
def sample_user_data():
    """Provide sample user data for tests."""
    return {
        "email": "test@example.com",
        "password": "TestPass123",
        "full_name": "Test User",
        "role": "user"
    }


@pytest.fixture
def sample_shop_data():
    """Provide sample shop data for tests."""
    return {
        "name": "Test Shop",
        "address": "123 Test Street",
        "city": "Test City",
        "country": "Test Country"
    }


@pytest.fixture
def sample_product_data():
    """Provide sample product data for tests."""
    return {
        "name": "Test Product",
        "sku": "TEST-001",
        "default_cost": 9.99
    }
