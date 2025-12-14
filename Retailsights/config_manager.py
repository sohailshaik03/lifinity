"""
Configuration management with environment-based settings
Follows 12-factor app methodology
"""
import os
from typing import Literal
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

Environment = Literal["development", "staging", "production"]


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    echo: bool
    
    @classmethod
    def from_env(cls, env: Environment) -> "DatabaseConfig":
        return cls(
            url=os.getenv("DATABASE_URL", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=env == "development"
        )


@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl: int  # Time to live in seconds
    max_size: int
    
    @classmethod
    def from_env(cls, env: Environment) -> "CacheConfig":
        return cls(
            ttl=int(os.getenv("CACHE_TTL", "300")),  # 5 minutes default
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000"))
        )


@dataclass
class SecurityConfig:
    """Security configuration"""
    session_timeout: int
    max_login_attempts: int
    password_min_length: int
    require_special_char: bool
    jwt_secret: str
    jwt_expiry: int
    
    @classmethod
    def from_env(cls, env: Environment) -> "SecurityConfig":
        return cls(
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600")),  # 1 hour
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            require_special_char=os.getenv("REQUIRE_SPECIAL_CHAR", "true").lower() == "true",
            jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production"),
            jwt_expiry=int(os.getenv("JWT_EXPIRY", "86400"))  # 24 hours
        )


@dataclass
class ObservabilityConfig:
    """Observability and monitoring configuration"""
    enable_metrics: bool
    enable_tracing: bool
    log_level: str
    sentry_dsn: str | None
    
    @classmethod
    def from_env(cls, env: Environment) -> "ObservabilityConfig":
        return cls(
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            enable_tracing=os.getenv("ENABLE_TRACING", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO" if env == "production" else "DEBUG"),
            sentry_dsn=os.getenv("SENTRY_DSN")
        )


@dataclass
class FeatureFlags:
    """Feature flags for gradual rollout"""
    enable_ai_features: bool
    enable_advanced_analytics: bool
    enable_blockchain: bool
    enable_iot_sensors: bool
    enable_payment_processing: bool
    
    @classmethod
    def from_env(cls) -> "FeatureFlags":
        return cls(
            enable_ai_features=os.getenv("FEATURE_AI", "true").lower() == "true",
            enable_advanced_analytics=os.getenv("FEATURE_ANALYTICS", "true").lower() == "true",
            enable_blockchain=os.getenv("FEATURE_BLOCKCHAIN", "false").lower() == "true",
            enable_iot_sensors=os.getenv("FEATURE_IOT", "false").lower() == "true",
            enable_payment_processing=os.getenv("FEATURE_PAYMENTS", "false").lower() == "true"
        )


@dataclass
class AppConfig:
    """Main application configuration"""
    env: Environment
    debug: bool
    database: DatabaseConfig
    cache: CacheConfig
    security: SecurityConfig
    observability: ObservabilityConfig
    features: FeatureFlags
    
    @classmethod
    def load(cls) -> "AppConfig":
        env = os.getenv("ENV", "development").lower()
        if env not in ("development", "staging", "production"):
            env = "development"
        
        return cls(
            env=env,  # type: ignore
            debug=env == "development",
            database=DatabaseConfig.from_env(env),  # type: ignore
            cache=CacheConfig.from_env(env),  # type: ignore
            security=SecurityConfig.from_env(env),  # type: ignore
            observability=ObservabilityConfig.from_env(env),  # type: ignore
            features=FeatureFlags.from_env()
        )


# Global config instance
config = AppConfig.load()
