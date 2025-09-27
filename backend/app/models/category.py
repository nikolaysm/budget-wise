"""
SQLModel definition for transaction categories.

A category represents a logical grouping of transactions, such as
"shopping", "food", or "travel". Each category has an auto‑incrementing
primary key and a unique name. The relationship to `Transaction` is
defined via the `transactions` attribute.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import model_validator
from slugify import slugify
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .transaction import Transaction


class CategoryBase(SQLModel):
    """Base attributes shared by models inheriting from Category."""

    name: str = Field(index=True, unique=True)
    slug: str | None = Field(
        default=None,
        index=True,
        unique=True,
        description="URL-friendly stable identifier derived from name",
    )

    @model_validator(mode="before")
    @classmethod
    def _generate_slug(cls, values: dict):  # type: ignore[override]
        if not values.get("slug"):
            name = values.get("name")
            generated = slugify(name)
            values["slug"] = generated.lower()
        return values


class Category(CategoryBase, table=True):
    """Database model for a transaction category."""

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Establish one‑to‑many relationship with Transaction
    transactions: Mapped[list[Transaction]] = Relationship(
        sa_relationship=relationship(back_populates="category")
    )


class CategoryOut(CategoryBase):
    """Lightweight read model for Category responses (includes slug)."""

    id: UUID

class CategoryIn(CategoryBase):
    """Input model for creating a category using the shared CategoryBase (name + slug)."""
    # Inherits name & slug (slug optional / auto-generated)
