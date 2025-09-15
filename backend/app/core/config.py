"""
Application settings and configuration.

This module defines a Pydantic `Settings` class used for storing application
configuration such as the database URL. It also provides a `get_settings`
function to retrieve the settings with caching to avoid re‑parsing the
environment on each call.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration values loaded from environment variables or defaults."""

    # Use case-insensitive env vars so DATABASE_URL works as expected
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "Budgt Wise"
    app_logger_name: str = "budget_wise"

    # Database URL in SQLAlchemy format
    # Example: postgresql+psycopg://user:password@localhost:5432/budget_db
    database_url: str = "sqlite:///./budget_wise.db"
    db_echo: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()


LOGGER_CONFIG = LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "format": "%(levelprefix)s %(asctime)s - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        get_settings().app_logger_name: {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
