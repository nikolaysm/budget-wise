"""
Dependency functions used in API routes.

These dependencies can be overridden in tests to provide test database
connections or mocked services.
"""

from collections.abc import Generator

from fastapi import Depends
from sqlmodel import Session

from app.daos.account_dao import AccountDAO
from app.daos.transaction_dao import TransactionDAO
from app.db.session import get_session
from app.services.transaction_service import TransactionService


def get_db() -> Generator[Session, None, None]:
    """Provide a database session dependency for route handlers."""
    yield from get_session()


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    """Provide a `TransactionService` with DAOs bound to the current session."""
    return TransactionService(TransactionDAO(db), AccountDAO(db), db)
