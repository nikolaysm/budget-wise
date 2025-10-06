"""Central dependency providers for API routes.

Simplified single module version requested by user.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlmodel import Session

from app.daos.account_dao import AccountDAO
from app.daos.category_dao import CategoryDAO
from app.daos.transaction_dao import TransactionDAO
from app.db.session import get_session
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""
    yield from get_session()


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    """Provide TransactionService bound to session."""
    return TransactionService(TransactionDAO(db), AccountDAO(db), CategoryDAO(db))


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """Provide CategoryService bound to session."""
    return CategoryService(CategoryDAO(db), TransactionDAO(db))
