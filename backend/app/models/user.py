"""
SQLModel definition for application users.

This model represents a user of the budgeting application. In a multi‑tenant
setup, each user can own multiple accounts and upload transaction files.
Passwords should be hashed before being stored in the database; never store
plaintext passwords.
"""

from __future__ import annotations

from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class UserBase(SQLModel):
    """Base attributes for User models."""

    email: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    is_active: bool = True


class User(UserBase, table=True):
    """Database model representing an application user."""

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    # One-to-many relationship: a user can have multiple accounts
    accounts: List["Account"] = Relationship(back_populates="user")