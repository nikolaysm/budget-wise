"""
SQLModel definition for transaction categories.

A category represents a logical grouping of transactions, such as
"shopping", "food", or "travel". Each category has an auto‑incrementing
primary key and a unique name. The relationship to `Transaction` is
defined via the `transactions` attribute.
"""

from __future__ import annotations

from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class CategoryBase(SQLModel):
    """Base attributes shared by models inheriting from Category."""

    name: str = Field(index=True, unique=True)


class Category(CategoryBase, table=True):
    """Database model for a transaction category."""

    id: Optional[int] = Field(default=None, primary_key=True)
    # Establish one‑to‑many relationship with Transaction
    transactions: List["Transaction"] = Relationship(back_populates="category")