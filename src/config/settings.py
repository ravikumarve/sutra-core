"""
SUTRA Core Configuration
Centralized configuration management with Pydantic settings
"""
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "SUTRA Core"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Meta WhatsApp Cloud API
    meta_app_id: str = Field(..., env="META_APP_ID")
    meta_app_secret: str = Field(..., env="META_APP_SECRET")
    meta_phone_number_id: str = Field(..., env="META_PHONE_NUMBER_ID")
    meta_verify_token: str = Field(..., env="META_VERIFY_TOKEN")
    meta_access_token: str = Field(..., env="META_ACCESS_TOKEN")
    meta_webhook_url: Optional[str] = Field(None, env="META_WEBHOOK_URL")
    
    # LLM APIs
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY")
    
    # Database
    database_url: str = Field(
        default="postgresql://sutra_user:yourpassword@localhost/sutra_db",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    database_pool_recycle: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_pool_size: int = Field(default=10, env="REDIS_POOL_SIZE")
    redis_stream_max_len: int = Field(default=10000, env="REDIS_STREAM_MAX_LEN")
    
    # Multi-tenancy
    default_tenant_id: str = Field(default="default", env="DEFAULT_TENANT_ID")
    tenant_isolation_enabled: bool = Field(default=True, env="TENANT_ISOLATION_ENABLED")
    
    # GST
    default_gst_state_code: str = Field(default="24", env="DEFAULT_GST_STATE_CODE")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=10000, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    # Encryption
    encryption_key: Optional[str] = Field(None, env="ENCRYPTION_KEY")
    
    # Monitoring
    monitoring_enabled: bool = Field(default=True, env="MONITORING_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    audit_logging_enabled: bool = Field(default=True, env="AUDIT_LOGGING_ENABLED")
    
    # Backup
    backup_enabled: bool = Field(default=True, env="BACKUP_ENABLED")
    backup_schedule: str = Field(default="0 2 * * *", env="BACKUP_SCHEDULE")
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    backup_path: str = Field(default="/var/backups/sutra", env="BACKUP_PATH")
    
    # Alerts
    restock_threshold_units: int = Field(default=10, env="RESTOCK_THRESHOLD_UNITS")
    udhaar_alert_days: int = Field(default=30, env="UDHAAR_ALERT_DAYS")
    
    # Performance
    max_request_size: int = Field(default=10485760, env="MAX_REQUEST_SIZE")  # 10MB
    max_webhook_retries: int = Field(default=3, env="MAX_WEBHOOK_RETRIES")
    webhook_timeout: int = Field(default=30, env="WEBHOOK_TIMEOUT")
    
    # Testing
    test_mode: bool = Field(default=False, env="TEST_MODE")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment is one of allowed values"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite://")):
            raise ValueError("database_url must start with postgresql://, postgresql+asyncpg://, or sqlite://")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"
    
    @property
    def DEBUG(self) -> bool:
        """Uppercase DEBUG property for compatibility"""
        return self.debug

    @property
    def ENVIRONMENT(self) -> str:
        """Uppercase ENVIRONMENT property for compatibility"""
        return self.environment

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Uppercase CORS_ORIGINS property for compatibility"""
        return self.cors_origins

    @property
    def META_APP_ID(self) -> str:
        """Uppercase META_APP_ID property for compatibility"""
        return self.meta_app_id

    @property
    def META_APP_SECRET(self) -> str:
        """Uppercase META_APP_SECRET property for compatibility"""
        return self.meta_app_secret

    @property
    def META_PHONE_NUMBER_ID(self) -> str:
        """Uppercase META_PHONE_NUMBER_ID property for compatibility"""
        return self.meta_phone_number_id

    @property
    def META_VERIFY_TOKEN(self) -> str:
        """Uppercase META_VERIFY_TOKEN property for compatibility"""
        return self.meta_verify_token

    @property
    def META_ACCESS_TOKEN(self) -> str:
        """Uppercase META_ACCESS_TOKEN property for compatibility"""
        return self.meta_access_token

    @property
    def META_WEBHOOK_URL(self) -> Optional[str]:
        """Uppercase META_WEBHOOK_URL property for compatibility"""
        return self.meta_webhook_url

    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        """Uppercase OPENAI_API_KEY property for compatibility"""
        return self.openai_api_key

    @property
    def GEMINI_API_KEY(self) -> Optional[str]:
        """Uppercase GEMINI_API_KEY property for compatibility"""
        return self.gemini_api_key

    @property
    def GROQ_API_KEY(self) -> Optional[str]:
        """Uppercase GROQ_API_KEY property for compatibility"""
        return self.groq_api_key

    @property
    def DATABASE_URL(self) -> str:
        """Uppercase DATABASE_URL property for compatibility"""
        return self.database_url

    @property
    def REDIS_URL(self) -> str:
        """Uppercase REDIS_URL property for compatibility"""
        return self.redis_url

    @property
    def REDIS_POOL_SIZE(self) -> int:
        """Uppercase REDIS_POOL_SIZE property for compatibility"""
        return self.redis_pool_size

    @property
    def REDIS_STREAM_MAX_LEN(self) -> int:
        """Uppercase REDIS_STREAM_MAX_LEN property for compatibility"""
        return self.redis_stream_max_len

    @property
    def DEFAULT_TENANT_ID(self) -> str:
        """Uppercase DEFAULT_TENANT_ID property for compatibility"""
        return self.default_tenant_id

    @property
    def TENANT_ISOLATION_ENABLED(self) -> bool:
        """Uppercase TENANT_ISOLATION_ENABLED property for compatibility"""
        return self.tenant_isolation_enabled

    @property
    def DEFAULT_GST_STATE_CODE(self) -> str:
        """Uppercase DEFAULT_GST_STATE_CODE property for compatibility"""
        return self.default_gst_state_code

    @property
    def SECRET_KEY(self) -> str:
        """Uppercase SECRET_KEY property for compatibility"""
        return self.secret_key

    @property
    def ALGORITHM(self) -> str:
        """Uppercase ALGORITHM property for compatibility"""
        return self.algorithm

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """Uppercase ACCESS_TOKEN_EXPIRE_MINUTES property for compatibility"""
        return self.access_token_expire_minutes

    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        """Uppercase REFRESH_TOKEN_EXPIRE_DAYS property for compatibility"""
        return self.refresh_token_expire_days

    @property
    def RATE_LIMIT_ENABLED(self) -> bool:
        """Uppercase RATE_LIMIT_ENABLED property for compatibility"""
        return self.rate_limit_enabled

    @property
    def RATE_LIMIT_REQUESTS(self) -> int:
        """Uppercase RATE_LIMIT_REQUESTS property for compatibility"""
        return self.rate_limit_requests

    @property
    def RATE_LIMIT_PERIOD(self) -> int:
        """Uppercase RATE_LIMIT_PERIOD property for compatibility"""
        return self.rate_limit_period

    @property
    def ENCRYPTION_KEY(self) -> Optional[str]:
        """Uppercase ENCRYPTION_KEY property for compatibility"""
        return self.encryption_key

    @property
    def MONITORING_ENABLED(self) -> bool:
        """Uppercase MONITORING_ENABLED property for compatibility"""
        return self.monitoring_enabled

    @property
    def PROMETHEUS_PORT(self) -> int:
        """Uppercase PROMETHEUS_PORT property for compatibility"""
        return self.prometheus_port

    @property
    def LOG_LEVEL(self) -> str:
        """Uppercase LOG_LEVEL property for compatibility"""
        return self.log_level

    @property
    def AUDIT_LOGGING_ENABLED(self) -> bool:
        """Uppercase AUDIT_LOGGING_ENABLED property for compatibility"""
        return self.audit_logging_enabled

    @property
    def BACKUP_ENABLED(self) -> bool:
        """Uppercase BACKUP_ENABLED property for compatibility"""
        return self.backup_enabled

    @property
    def BACKUP_SCHEDULE(self) -> str:
        """Uppercase BACKUP_SCHEDULE property for compatibility"""
        return self.backup_schedule

    @property
    def BACKUP_RETENTION_DAYS(self) -> int:
        """Uppercase BACKUP_RETENTION_DAYS property for compatibility"""
        return self.backup_retention_days

    @property
    def BACKUP_PATH(self) -> str:
        """Uppercase BACKUP_PATH property for compatibility"""
        return self.backup_path

    @property
    def RESTOCK_THRESHOLD_UNITS(self) -> int:
        """Uppercase RESTOCK_THRESHOLD_UNITS property for compatibility"""
        return self.restock_threshold_units

    @property
    def UDHAAR_ALERT_DAYS(self) -> int:
        """Uppercase UDHAAR_ALERT_DAYS property for compatibility"""
        return self.udhaar_alert_days

    @property
    def MAX_REQUEST_SIZE(self) -> int:
        """Uppercase MAX_REQUEST_SIZE property for compatibility"""
        return self.max_request_size

    @property
    def MAX_WEBHOOK_RETRIES(self) -> int:
        """Uppercase MAX_WEBHOOK_RETRIES property for compatibility"""
        return self.max_webhook_retries

    @property
    def WEBHOOK_TIMEOUT(self) -> int:
        """Uppercase WEBHOOK_TIMEOUT property for compatibility"""
        return self.webhook_timeout

    @property
    def TEST_MODE(self) -> bool:
        """Uppercase TEST_MODE property for compatibility"""
        return self.test_mode
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL (handles both PostgreSQL and SQLite)"""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://")
        if url.startswith("sqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance (for dependency injection)"""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)"""
    global settings
    settings = Settings()
    return settings