"""
Configuration validation for the Django application

This module provides defensive programming patterns for validating
critical application settings at startup.
"""

import logging
import os
from collections.abc import Callable
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails"""

    pass


def validate_configuration() -> None:
    """
    Validate critical configuration settings at startup.

    This function should be called during Django app initialization
    to ensure all required settings are properly configured.

    Raises:
        ConfigurationValidationError: If any critical setting is invalid
    """
    logger.info("Starting configuration validation...")

    # Define required settings with their types and validation functions
    required_settings: list[tuple[str, type, Callable[[Any], None]]] = [
        ("SECRET_KEY", str, _validate_secret_key),
        # ('DATABASE_URL', str, _validate_database_url),  # Commented out as requested
        ("DEBUG", bool, _validate_debug_setting),
        ("ALLOWED_HOSTS", list, _validate_allowed_hosts),
        ("TIME_ZONE", str, _validate_timezone),
    ]

    # Optional but recommended settings
    recommended_settings: list[tuple[str, type, Callable[[Any], None]]] = [
        ("EMAIL_HOST", str, _validate_email_host),
        ("MEDIA_ROOT", str, _validate_media_root),
        ("STATIC_ROOT", str, _validate_static_root),
        ("LOGGING", dict, _validate_logging_config),
    ]

    validation_errors = []
    validation_warnings = []

    # Validate required settings
    for setting_name, expected_type, validator in required_settings:
        try:
            _validate_setting(setting_name, expected_type, validator, required=True)
            logger.debug(f"✓ {setting_name} validation passed")
        except ConfigurationValidationError as e:
            validation_errors.append(str(e))
            logger.error(f"✗ {setting_name} validation failed: {e}")

    # Validate recommended settings
    for setting_name, expected_type, validator in recommended_settings:
        try:
            _validate_setting(setting_name, expected_type, validator, required=False)
            logger.debug(f"✓ {setting_name} validation passed")
        except ConfigurationValidationError as e:
            validation_warnings.append(str(e))
            logger.warning(f"⚠ {setting_name} validation warning: {e}")

    # Check environment-specific settings
    _validate_environment_settings(validation_errors, validation_warnings)

    # Log validation results
    if validation_errors:
        error_msg = (
            f"Configuration validation failed with {len(validation_errors)} critical errors:\n"
            + "\n".join(f"  - {error}" for error in validation_errors)
        )
        logger.error(error_msg)
        raise ConfigurationValidationError(error_msg)

    if validation_warnings:
        warning_msg = (
            f"Configuration validation completed with {len(validation_warnings)} warnings:\n"
            + "\n".join(f"  - {warning}" for warning in validation_warnings)
        )
        logger.warning(warning_msg)

    logger.info(
        f"✓ Configuration validation completed successfully "
        f"({len(validation_warnings)} warnings)"
    )


def _validate_setting(
    setting_name: str,
    expected_type: type,
    validator: Callable[[Any], None],
    required: bool = True,
) -> None:
    """Validate a single setting"""
    try:
        value = getattr(settings, setting_name, None)
    except AttributeError as e:
        if required:
            raise ConfigurationValidationError(f"{setting_name} is not set") from e
        return

    if value is None:
        if required:
            raise ConfigurationValidationError(f"{setting_name} is not set")
        return

    if not isinstance(value, expected_type):
        raise ConfigurationValidationError(
            f"{setting_name} must be {expected_type.__name__}, got {type(value).__name__}"
        )

    # Run custom validator
    try:
        validator(value)
    except Exception as e:
        raise ConfigurationValidationError(f"{setting_name} failed validation: {e}") from e


def _validate_secret_key(secret_key: str) -> None:
    """Validate Django SECRET_KEY"""
    if len(secret_key) < 50:
        raise ConfigurationValidationError(
            "SECRET_KEY should be at least 50 characters long"
        )

    if secret_key == "django-insecure-" + "x" * 40:  # Default Django key pattern
        raise ConfigurationValidationError(
            "SECRET_KEY appears to be the default insecure key"
        )

    # Check for reasonable complexity
    if secret_key.isalnum():
        raise ConfigurationValidationError(
            "SECRET_KEY should contain special characters"
        )


def _validate_database_url(database_url: str) -> None:
    """Validate database URL format"""
    valid_prefixes = (
        "postgresql://",
        "postgres://",
        "mysql://",
        "sqlite://",
        "sqlite:///",
    )

    if not any(database_url.startswith(prefix) for prefix in valid_prefixes):
        raise ConfigurationValidationError(
            f"DATABASE_URL must start with one of: {', '.join(valid_prefixes)}"
        )

    # Additional checks for production databases
    if not settings.DEBUG and database_url.startswith("sqlite://"):
        raise ConfigurationValidationError("SQLite should not be used in production")


def _validate_debug_setting(debug: bool) -> None:
    """Validate DEBUG setting based on environment"""
    # In production-like environments, DEBUG should be False
    env = os.environ.get("DJANGO_ENV", "development").lower()

    if env in ["production", "prod"] and debug:
        raise ConfigurationValidationError("DEBUG should be False in production")


def _validate_allowed_hosts(allowed_hosts: list) -> None:
    """Validate ALLOWED_HOSTS setting"""
    if not settings.DEBUG and not allowed_hosts:
        raise ConfigurationValidationError(
            "ALLOWED_HOSTS cannot be empty when DEBUG=False"
        )

    # Check for wildcard in production
    if not settings.DEBUG and "*" in allowed_hosts:
        raise ConfigurationValidationError(
            "ALLOWED_HOSTS should not contain '*' in production"
        )

    # Validate host format
    for host in allowed_hosts:
        if not isinstance(host, str):
            raise ConfigurationValidationError(
                "All entries in ALLOWED_HOSTS must be strings"
            )

        if host and not (
            host == "*"
            or host == "localhost"
            or "." in host
            or host.startswith("127.")
            or host.startswith("192.168.")
        ):
            # Basic host format validation
            pass  # Could add more sophisticated validation here


def _validate_timezone(timezone: str) -> None:
    """Validate TIME_ZONE setting"""
    import zoneinfo

    try:
        zoneinfo.ZoneInfo(timezone)
    except zoneinfo.ZoneInfoNotFoundError as e:
        raise ConfigurationValidationError(f"Invalid timezone: {timezone}") from e


def _validate_email_host(email_host: str) -> None:
    """Validate email host setting"""
    if email_host and not ("." in email_host or email_host == "localhost"):
        raise ConfigurationValidationError("EMAIL_HOST should be a valid hostname")


def _validate_media_root(media_root: str) -> None:
    """Validate MEDIA_ROOT setting"""
    if not os.path.isabs(media_root):
        raise ConfigurationValidationError("MEDIA_ROOT should be an absolute path")

    # Try to create directory if it doesn't exist
    try:
        os.makedirs(media_root, exist_ok=True)
        # Test write permissions
        test_file = os.path.join(media_root, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except (OSError, PermissionError) as e:
        raise ConfigurationValidationError(f"MEDIA_ROOT is not writable: {e}") from e


def _validate_static_root(static_root: str) -> None:
    """Validate STATIC_ROOT setting"""
    if not settings.DEBUG and static_root:
        if not os.path.isabs(static_root):
            raise ConfigurationValidationError("STATIC_ROOT should be an absolute path")


def _validate_logging_config(logging_config: dict) -> None:
    """Validate logging configuration"""
    if "version" not in logging_config:
        raise ConfigurationValidationError(
            "LOGGING configuration must include 'version'"
        )

    if logging_config.get("version") != 1:
        raise ConfigurationValidationError("LOGGING configuration version must be 1")


def _validate_environment_settings(errors: list, warnings: list) -> None:
    """Validate environment-specific settings"""
    env = os.environ.get("DJANGO_ENV", "development").lower()

    if env in ["production", "prod"]:
        # Production-specific validations
        if (
            not hasattr(settings, "SECURE_SSL_REDIRECT")
            or not settings.SECURE_SSL_REDIRECT
        ):
            warnings.append("SECURE_SSL_REDIRECT should be True in production")

        if (
            not hasattr(settings, "SECURE_HSTS_SECONDS")
            or settings.SECURE_HSTS_SECONDS < 31536000
        ):
            warnings.append(
                "SECURE_HSTS_SECONDS should be at least 31536000 (1 year) in production"
            )

        if (
            not hasattr(settings, "SESSION_COOKIE_SECURE")
            or not settings.SESSION_COOKIE_SECURE
        ):
            warnings.append("SESSION_COOKIE_SECURE should be True in production")

        if (
            not hasattr(settings, "CSRF_COOKIE_SECURE")
            or not settings.CSRF_COOKIE_SECURE
        ):
            warnings.append("CSRF_COOKIE_SECURE should be True in production")

    # Check for common security headers
    security_middleware = "django.middleware.security.SecurityMiddleware"
    if hasattr(settings, "MIDDLEWARE"):
        if security_middleware not in settings.MIDDLEWARE:
            warnings.append(f"{security_middleware} not found in MIDDLEWARE")


def validate_database_connection() -> None:
    """
    Validate database connection is working.

    This should be called separately from main configuration validation
    as it requires Django to be fully initialized.
    """
    try:
        from django.db import connections
        from django.db.utils import OperationalError

        db_conn = connections["default"]
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result != (1,):
                raise ConfigurationValidationError("Database connection test failed")

        logger.info("✓ Database connection validated successfully")

    except OperationalError as e:
        raise ConfigurationValidationError(f"Cannot connect to database: {e}") from e
    except Exception as e:
        raise ConfigurationValidationError(f"Database validation failed: {e}") from e


def get_configuration_summary() -> dict:
    """
    Get a summary of current configuration for monitoring/debugging.

    Returns a dictionary with non-sensitive configuration information.
    """
    summary = {
        "debug": getattr(settings, "DEBUG", None),
        "database_engine": None,
        "cache_backend": None,
        "time_zone": getattr(settings, "TIME_ZONE", None),
        "language_code": getattr(settings, "LANGUAGE_CODE", None),
        "static_url": getattr(settings, "STATIC_URL", None),
        "media_url": getattr(settings, "MEDIA_URL", None),
        "allowed_hosts_count": len(getattr(settings, "ALLOWED_HOSTS", [])),
        "middleware_count": len(getattr(settings, "MIDDLEWARE", [])),
        "installed_apps_count": len(getattr(settings, "INSTALLED_APPS", [])),
    }

    # Get database engine safely
    try:
        databases = getattr(settings, "DATABASES", {})
        default_db = databases.get("default", {})
        summary["database_engine"] = default_db.get("ENGINE", "unknown")
    except Exception:
        summary["database_engine"] = "error_reading_config"

    # Get cache backend safely
    try:
        caches = getattr(settings, "CACHES", {})
        default_cache = caches.get("default", {})
        summary["cache_backend"] = default_cache.get("BACKEND", "unknown")
    except Exception:
        summary["cache_backend"] = "error_reading_config"

    return summary


if __name__ == "__main__":
    # Allow running this module directly for testing
    try:
        validate_configuration()
        print("✓ Configuration validation passed")

        summary = get_configuration_summary()
        print("\nConfiguration Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

    except ConfigurationValidationError as e:
        print(f"✗ Configuration validation failed: {e}")
        exit(1)
