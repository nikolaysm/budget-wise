"""Sorting parameters schema and conversion utility."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SortParams(BaseModel):
    """Single-field sorting (field + direction)."""

    sort_by: str | None = Field(None, description="Field name to sort by")
    sort_dir: Literal["asc", "desc"] | None = Field(
        None, description="Sort direction for sort_by (asc/desc)"
    )

    def to_sorts(self, *, default: list[str] | None = None) -> list[str]:
        """Convert to the list[str] form used by generic_filters."""
        if not self.sort_by:
            return list(default or [])
        direction = (self.sort_dir or "asc").lower()
        return [f"{self.sort_by}:{direction}"]
