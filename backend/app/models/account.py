"""
SQLModel definition for bank accounts.

An account belongs to a user and can have many transactions. This model can be
extended to include additional metadata such as bank name or IBAN.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .transaction import Transaction
    from .user import User


class AccountBase(SQLModel):
    """Base attributes for the Account model."""

    number: str = Field(index=True)
    bic: str | None = None
    bank_name: str | None = None
    currency: str | None = None


class Account(AccountBase, table=True):
    """Database model representing a bank account."""

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID | None = Field(default=None, foreign_key="user.id")
    # Relationships
    user: Mapped[User | None] = Relationship(
        sa_relationship=relationship(back_populates="accounts")
    )
    # A one-to-many relationship to `Transaction`. The corresponding attribute on
    # Transaction is `account_ref` to avoid name clashes with the raw `account` field.
    transactions: Mapped[list[Transaction]] = Relationship(
        sa_relationship=relationship(back_populates="account_ref")
    )
