"""
CRUD utilities for the `Transaction` model.

These functions provide a layer of abstraction over the raw SQLModel API,
encouraging consistent usage patterns and simplifying future refactoring.
"""

from typing import List, Optional

from sqlmodel import Session, select

from app.models.transaction import Transaction


def create_transaction(db: Session, *, transaction: Transaction) -> Transaction:
    """Insert a new `Transaction` into the database.

    Args:
        db (Session): A database session.
        transaction (Transaction): The transaction instance to add.

    Returns:
        Transaction: The persisted transaction with an assigned primary key.
    """
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_transaction(db: Session, *, transaction_id: int) -> Optional[Transaction]:
    """Retrieve a single transaction by ID.

    Args:
        db (Session): A database session.
        transaction_id (int): Primary key of the transaction.

    Returns:
        Optional[Transaction]: The transaction if found, else `None`.
    """
    return db.get(Transaction, transaction_id)


def get_transactions(db: Session, *, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """Return a list of transactions with pagination.

    Args:
        db (Session): A database session.
        skip (int, optional): Offset for the first result. Defaults to 0.
        limit (int, optional): Maximum number of results. Defaults to 100.

    Returns:
        List[Transaction]: A list of transactions.
    """
    statement = select(Transaction).offset(skip).limit(limit)
    return list(db.exec(statement))