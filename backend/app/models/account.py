"""
SQLModel definition for bank accounts.

An account belongs to a user and can have many transactions. This model can be
extended to include additional metadata such as bank name or IBAN.
"""

from __future__ import annotations

from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class AccountBase(SQLModel):
    """Base attributes for the Account model."""

    number: str = Field(index=True)
    bic: Optional[str] = None
    bank_name: Optional[str] = None
    currency: Optional[str] = None


class Account(AccountBase, table=True):
    """Database model representing a bank account."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    # Relationships
    user: Optional["User"] = Relationship(back_populates="accounts")
    # A one-to-many relationship to `Transaction`. The corresponding attribute on
    # Transaction is `account_ref` to avoid name clashes with the raw `account` field.
    transactions: List["Transaction"] = Relationship(back_populates="account_ref")