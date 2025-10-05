"""Reusable pagination schemas.

Provides a request input model (PaginationIn) and a generic output model (PaginationOut)
that carries items plus navigation links (next / previous) and optional total count.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field, computed_field

T = TypeVar("T")


class PaginationIn(BaseModel):
    """Incoming pagination parameters (offset-based)."""

    offset: int = Field(
        0, ge=0, description="Number of items to skip before starting to collect the result set"
    )
    limit: int = Field(100, ge=1, le=500, description="Maximum number of items to return")


class PaginationOut(BaseModel, Generic[T]):
    """Standard pagination envelope with computed navigation links.

    Provide `has_next` / `has_previous` hints and derive URLs externally by supplying a base_url
    when serializing if needed. For now, compute next/previous offsets only.
    """

    items: list[T]
    offset: int
    limit: int
    total: int | None = None  # Can be set if/when a COUNT(*) is performed
    # Flag from caller indicating more items existed beyond this page (caller fetched limit+1)
    has_more: bool = False

    @computed_field  # type: ignore[misc]
    @property
    def next(self) -> int | None:  # returning offset for next page
        if self.has_more:
            return self.offset + self.limit
        return None

    @computed_field  # type: ignore[misc]
    @property
    def previous(self) -> int | None:  # returning offset for previous page
        if self.offset <= 0:
            return None
        return max(self.offset - self.limit, 0)


# Convenience concrete alias pattern (optional)
# from app.models.transaction import Transaction  # circular if imported here eagerly
# TransactionPage = PaginationOut[Transaction]
