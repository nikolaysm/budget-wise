"""
Database session and engine configuration.

This module creates a SQLAlchemy engine via SQLModel and exposes a
dependency function for obtaining a database session within FastAPI routes.
"""

from typing import Generator

from sqlmodel import create_engine, Session

from app.core.config import get_settings


settings = get_settings()

# The SQLModel engine is created once per process. For SQLite this will
# create a local file. For production use, configure DATABASE_URL via
# environment variables.
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,
)


def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.

    Yields a SQLModel `Session` and ensures it is closed after use.

    Yields:
        Generator[Session, None, None]: A database session.
    """
    with Session(engine) as session:
        yield session