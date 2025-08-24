"""
Alembic migration environment.

This script configures the context for Alembic migrations. It sets up the
SQLAlchemy engine using the `DATABASE_URL` from our Pydantic settings and
exposes the SQLModel metadata to autogenerate migrations.
"""

from __future__ import annotations

import sys
from typing import Any, Dict
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))  # noqa: E402

from app.core.config import get_settings  # noqa: E402
import app.models.transaction  # noqa: F401  # ensure Transaction model is loaded
import app.models.category  # noqa: F401  # ensure Category model is loaded
import app.models.user  # noqa: F401  # ensure User model is loaded
import app.models.account  # noqa: F401  # ensure Account model is loaded


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging if present.
if config.config_file_name:
    fileConfig(config.config_file_name)

# Grab the metadata for 'autogenerate'
target_metadata = SQLModel.metadata

# Use the database URL from our settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # Ensure configuration is a concrete dict for typing
    configuration: Dict[str, Any] = dict(config.get_section(config.config_ini_section) or {})
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()