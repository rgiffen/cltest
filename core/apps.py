import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self) -> None:
        """
        Called when Django has loaded all models and is ready to start.
        Perfect place for configuration validation and defensive checks.
        """
        # Only run validation once and not during migrations
        import sys

        if "migrate" not in sys.argv and "makemigrations" not in sys.argv:
            try:
                from config.validation import (
                    get_configuration_summary,
                    validate_configuration,
                )

                # Validate critical configuration
                validate_configuration()

                # Log configuration summary for monitoring
                config_summary = get_configuration_summary()
                logger.info(
                    "Application started with configuration summary",
                    extra=config_summary,
                )

            except Exception as e:
                # Log error but don't crash the application in development
                logger.error(f"Configuration validation failed: {e}", exc_info=True)

                # In production, you might want to raise the exception to prevent startup
                # if not settings.DEBUG:
                #     raise
