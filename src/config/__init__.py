"""
Configuration package for IAM Policy Classifier.

Exports a singleton 'settings' instance that can be imported throughout the application.

Usage:
    from src.config import settings

    # Access configuration values
    api_key = settings.ANTHROPIC_API_KEY
    env = settings.ENVIRONMENT
    log_level = settings.LOG_LEVEL

    # Use helper methods
    if settings.is_production():
        # Production-specific logic
        pass

    providers = settings.get_available_providers()
"""

from src.config.settings import settings, validate_settings

__all__ = ["settings", "validate_settings"]
