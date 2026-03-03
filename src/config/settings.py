"""
Configuration management for IAM Policy Classifier.

This module provides type-safe configuration loading from environment variables
using Pydantic BaseSettings. All settings are validated on application startup.

Usage:
    from src.config import settings

    api_key = settings.ANTHROPIC_API_KEY
    env = settings.ENVIRONMENT
"""

import logging
from typing import Optional, List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings are loaded from:
    1. Environment variables
    2. .env file (if present)
    3. Default values (where specified)

    At least one LLM API key must be provided (Anthropic or OpenAI).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )

    # ============================================================================
    # Application Metadata
    # ============================================================================

    APP_NAME: str = "IAM Policy Classifier"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # development, staging, production

    # ============================================================================
    # LLM API Keys (at least one required)
    # ============================================================================

    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # ============================================================================
    # LLM Configuration
    # ============================================================================

    # Default LLM provider to use if not specified
    DEFAULT_LLM_PROVIDER: str = "claude"  # claude or openai

    # Model names
    CLAUDE_MODEL: str = "claude-sonnet-4-5"
    OPENAI_MODEL: str = "gpt-4o"

    # LLM API timeouts (seconds)
    LLM_TIMEOUT: int = 30

    # Maximum tokens for LLM responses
    MAX_TOKENS: int = 1024

    # Temperature for LLM responses (0.0 = deterministic, 1.0 = creative)
    LLM_TEMPERATURE: float = 0.1

    # ============================================================================
    # API Rate Limiting
    # ============================================================================

    # Maximum requests per minute
    API_RATE_LIMIT: int = 10

    # Rate limit window in seconds
    RATE_LIMIT_WINDOW: int = 60

    # ============================================================================
    # Logging Configuration
    # ============================================================================

    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Log format
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Log to file (optional)
    LOG_FILE: Optional[str] = None

    # Enable JSON structured logging
    LOG_JSON: bool = False

    # CloudWatch log group name
    LOG_GROUP_NAME: str = "iam-policy-classifier"

    # CloudWatch log stream name template.
    # Supports {environment} and {hostname} placeholders resolved at startup.
    LOG_STREAM_NAME: str = "{environment}-{hostname}"

    # ============================================================================
    # CORS Configuration
    # ============================================================================

    # Allowed origins for CORS (comma-separated in .env)
    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Allow credentials in CORS
    CORS_ALLOW_CREDENTIALS: bool = True

    # Allowed HTTP methods
    CORS_ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

    # Allowed headers
    CORS_ALLOWED_HEADERS: List[str] = ["*"]

    # ============================================================================
    # Security
    # ============================================================================

    # Secret key for session management (optional, for future use)
    SECRET_KEY: Optional[str] = None

    # Enable API key authentication (for future use)
    ENABLE_API_AUTH: bool = False

    # ============================================================================
    # Database Configuration (Future Use - Placeholder)
    # ============================================================================

    # PostgreSQL connection string (optional)
    DATABASE_URL: Optional[str] = None

    # Database connection pool size
    DB_POOL_SIZE: int = 5

    # Database connection timeout (seconds)
    DB_TIMEOUT: int = 10

    # ============================================================================
    # Redis Configuration (Future Use - Placeholder)
    # ============================================================================

    # Redis connection string (optional)
    REDIS_URL: Optional[str] = None

    # Redis cache TTL (seconds)
    CACHE_TTL: int = 3600

    # ============================================================================
    # Validators
    # ============================================================================

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate that environment is one of the allowed values."""
        allowed = ["development", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(
                f"ENVIRONMENT must be one of {allowed}, got: {v}"
            )
        return v.lower()

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that log level is valid."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(
                f"LOG_LEVEL must be one of {allowed}, got: {v}"
            )
        return v_upper

    @field_validator("DEFAULT_LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate that default LLM provider is supported."""
        allowed = ["claude", "openai"]
        if v.lower() not in allowed:
            raise ValueError(
                f"DEFAULT_LLM_PROVIDER must be one of {allowed}, got: {v}"
            )
        return v.lower()

    @field_validator("API_RATE_LIMIT")
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        """Validate that rate limit is positive."""
        if v <= 0:
            raise ValueError("API_RATE_LIMIT must be positive")
        return v

    @field_validator("LLM_TEMPERATURE")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate that temperature is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("LLM_TEMPERATURE must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def validate_api_keys(self) -> "Settings":
        """
        Validate that at least one LLM API key is provided.

        At least one of ANTHROPIC_API_KEY or OPENAI_API_KEY must be set.
        """
        if not self.ANTHROPIC_API_KEY and not self.OPENAI_API_KEY:
            raise ValueError(
                "At least one LLM API key must be provided. "
                "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file."
            )
        return self

    @model_validator(mode="after")
    def validate_default_provider_key(self) -> "Settings":
        """
        Validate that the default provider has an API key.

        If DEFAULT_LLM_PROVIDER is set to 'claude', ANTHROPIC_API_KEY must be set.
        If DEFAULT_LLM_PROVIDER is set to 'openai', OPENAI_API_KEY must be set.
        """
        if self.DEFAULT_LLM_PROVIDER == "claude" and not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "DEFAULT_LLM_PROVIDER is 'claude' but ANTHROPIC_API_KEY is not set"
            )
        if self.DEFAULT_LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError(
                "DEFAULT_LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set"
            )
        return self

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def get_log_level_int(self) -> int:
        """
        Get the numeric log level for Python's logging module.

        Returns:
            int: Numeric log level (e.g., logging.INFO)
        """
        return getattr(logging, self.LOG_LEVEL)

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENVIRONMENT == "staging"

    def get_cors_origins(self) -> List[str]:
        """
        Get CORS allowed origins.

        In production, only return explicitly configured origins.
        In development, allow localhost variations.

        Returns:
            List[str]: List of allowed origins
        """
        if self.is_production():
            return self.CORS_ALLOWED_ORIGINS

        # In development, add common localhost variations
        dev_origins = set(self.CORS_ALLOWED_ORIGINS)
        dev_origins.update([
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000"
        ])
        return list(dev_origins)

    def has_anthropic_key(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self.ANTHROPIC_API_KEY)

    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.OPENAI_API_KEY)

    def get_available_providers(self) -> List[str]:
        """
        Get list of available LLM providers based on configured API keys.

        Returns:
            List[str]: List of provider names ('claude', 'openai')
        """
        providers = []
        if self.has_anthropic_key():
            providers.append("claude")
        if self.has_openai_key():
            providers.append("openai")
        return providers

    def model_dump_safe(self) -> dict:
        """
        Dump settings to dict with sensitive values redacted.

        Useful for logging configuration without exposing secrets.

        Returns:
            dict: Settings dictionary with secrets redacted
        """
        dump = self.model_dump()

        # Redact sensitive values
        sensitive_keys = [
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL"
        ]

        for key in sensitive_keys:
            if key in dump and dump[key]:
                # Show first 4 chars, redact rest
                value = dump[key]
                if len(value) > 4:
                    dump[key] = f"{value[:4]}...{'*' * 8}"
                else:
                    dump[key] = "***"

        return dump


# ============================================================================
# Singleton Instance
# ============================================================================

# Create a single settings instance that will be imported throughout the app
# This will load and validate settings on first import
settings = Settings()


# ============================================================================
# Startup Validation
# ============================================================================

def validate_settings() -> None:
    """
    Validate settings and log configuration.

    This function should be called at application startup to ensure
    all settings are valid before the app starts processing requests.
    """
    try:
        # Settings are already validated by Pydantic on instantiation
        # This function just provides a hook for additional startup checks

        # Log configuration (with secrets redacted)
        print("=" * 80)
        print("APPLICATION CONFIGURATION")
        print("=" * 80)
        print(f"App Name:        {settings.APP_NAME}")
        print(f"Version:         {settings.APP_VERSION}")
        print(f"Environment:     {settings.ENVIRONMENT}")
        print(f"Log Level:       {settings.LOG_LEVEL}")
        print(f"Default LLM:     {settings.DEFAULT_LLM_PROVIDER}")
        print(f"Available LLMs:  {', '.join(settings.get_available_providers())}")
        print(f"Rate Limit:      {settings.API_RATE_LIMIT} req/min")
        print(f"CORS Origins:    {len(settings.get_cors_origins())} configured")

        if settings.DATABASE_URL:
            print(f"Database:        Configured")
        if settings.REDIS_URL:
            print(f"Redis:           Configured")

        print("=" * 80)
        print("✓ Configuration validated successfully")
        print("=" * 80)

    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        raise


if __name__ == "__main__":
    # When run directly, validate and display settings
    validate_settings()

    print("\nDetailed Configuration (secrets redacted):")
    print("-" * 80)

    safe_config = settings.model_dump_safe()
    for key, value in sorted(safe_config.items()):
        print(f"{key:30} = {value}")
