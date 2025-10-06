"""
SQLModel definition for application users.

This model represents a user of the budgeting application. In a multi‑tenant
setup, each user can own multiple accounts and upload transaction files.
Passwords should be hashed before being stored in the database; never store
plaintext passwords.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .account import Account


class UserBase(SQLModel):
    """Base attributes for User models."""

    email: str = Field(index=True, unique=True)
    full_name: str | None = None
    is_active: bool = True


class User(UserBase, table=True):
    """Database model representing an application user."""

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    # One-to-many relationship: a user can have multiple accounts
    accounts: Mapped[list[Account]] = Relationship(
        sa_relationship=relationship(back_populates="user")
    )
