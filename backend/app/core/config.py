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

    # Database URL in SQLAlchemy format
    # Example: postgresql+psycopg://user:password@localhost:5432/budget_db
    database_url: str = "postPgresql+psycopg://budget_user:budget_pass@localhost:5432/budget_db"

    # Pydantic v2 settings configuration
    # Use case-insensitive env vars so DATABASE_URL works as expected
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()