"""Configuration management for RetailSights application.

Handles environment variables, database configuration, and application settings.
Supports both DATABASE_URL and individual DB connection parameters.
"""
import os
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from loguru import logger

load_dotenv()


class Config:
    """Application configuration class.
    
    Loads configuration from environment variables with sensible defaults.
    Supports both DATABASE_URL (e.g., Neon, Heroku) and individual DB parameters.
    """
    
    ENV: str = os.getenv("ENV", "development")
    
    # Database configuration
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    if DATABASE_URL:
        parsed = urlparse(DATABASE_URL)
        DB_HOST: str = parsed.hostname or "localhost"
        DB_USER: str = parsed.username or "root"
        DB_PASSWORD: str = parsed.password or ""
        DB_NAME: str = parsed.path.lstrip("/") or "retailsight"
        DB_PORT: int = parsed.port or 5432
    else:
        DB_HOST: str = os.getenv("DB_HOST", "localhost")
        DB_USER: str = os.getenv("DB_USER", "root")
        DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        DB_NAME: str = os.getenv("DB_NAME", "lifinity")
        DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Redis configuration
    UPSTASH_REDIS_REST_URL: Optional[str] = os.getenv("UPSTASH_REDIS_REST_URL")
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    REDIS_HOST: Optional[str] = os.getenv("REDIS_HOST")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Session configuration
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "change-me-in-production")
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "1440"))  # 24 hours
    
    # OpenAI configuration (for AI features)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Stripe payment configuration (UK client)
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_CURRENCY: str = os.getenv("STRIPE_CURRENCY", "gbp")  # UK default
    STRIPE_COUNTRY: str = os.getenv("STRIPE_COUNTRY", "GB")  # United Kingdom
    
    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration parameters.
        
        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        if not cls.DB_HOST:
            raise ValueError("DB_HOST is required")
        if not cls.DB_NAME:
            raise ValueError("DB_NAME is required")
        if cls.ENV == "production" and cls.SESSION_SECRET_KEY == "change-me-in-production":
            raise ValueError("SESSION_SECRET_KEY must be changed in production")
        
        logger.info(f"Configuration loaded - Environment: {cls.ENV}")
        logger.info(f"Database: {cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
        if cls.UPSTASH_REDIS_REST_URL:
            logger.info("Redis: Upstash REST API configured")
        elif cls.REDIS_HOST:
            logger.info(f"Redis: {cls.REDIS_HOST}:{cls.REDIS_PORT}")


config = Config()

# Validate configuration on import
try:
    config.validate()
except ValueError as e:
    logger.warning(f"Configuration validation warning: {e}")
