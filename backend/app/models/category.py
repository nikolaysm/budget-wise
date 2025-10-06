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
from sqlalchemy import Column, Text
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel

try:  # Prefer JSONB on PostgreSQL
    from sqlalchemy.dialects.postgresql import JSONB  # type: ignore

    JSONTypeUnified = JSONB  # pragma: no cover
except Exception:  # pragma: no cover - fallback for non-Postgres (e.g. SQLite during tests)
    from sqlalchemy.types import JSON  # type: ignore

    JSONTypeUnified = JSON  # pragma: no cover

if TYPE_CHECKING:
    from .transaction import Transaction


class CategoryBase(SQLModel):
    """Base attributes shared by models inheriting from Category.

    Attributes:
        name (str): The unique name of the category.
        slug (str | None): A URL-friendly stable identifier derived from the name.
        expanded_phrase (str | None): An optional richer/canonical phrase used for ML classification (falls back to name if absent).
        aliases (list[str]): A list of synonym labels (multi-language) to expand candidate set during classification.
    """

    name: str = Field(index=True, unique=True)
    slug: str | None = Field(
        default=None,
        index=True,
        unique=True,
        description="URL-friendly stable identifier derived from name",
    )
    expanded_phrase: str | None = Field(
        default=None,
        description="Optional richer / canonical phrase used for ML classification (falls back to name if absent)",
        sa_column=Column(Text),
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="List of synonym labels (multi-language) to expand candidate set during classification",
        sa_column=Column(JSONTypeUnified(), nullable=False, server_default="[]"),
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
    """Lightweight read model for Category responses (includes slug).
    Attributes:
        id (UUID): The unique identifier of the category.
    Inherits name, slug, expanded_phrase, aliases from CategoryBase.
    """

    id: UUID


class CategoryIn(CategoryBase):
    """Input model for creating a category using the shared CategoryBase (name + slug)."""

    # Inherits name & slug (slug optional / auto-generated)
