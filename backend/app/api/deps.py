"""
Dependency functions used in API routes.

These dependencies can be overridden in tests to provide test database
connections or mocked services.
"""

from typing import Generator

from sqlmodel import Session

from app.db.session import get_session


def get_db() -> Generator[Session, None, None]:
    """Provide a database session dependency for route handlers."""
    yield from get_session()