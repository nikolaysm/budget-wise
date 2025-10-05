"""API request body schemas for Category-related operations that are not covered by model I/O classes.

Currently only assignment payloads live here. Read / write models moved to `app.models.category`.
"""

from __future__ import annotations

from pydantic import UUID4, BaseModel, Field


class CategoryAssign(BaseModel):
    category: str = Field(
        min_length=1,
        max_length=128,
        description="Existing category name to assign (no automatic creation)",
    )


class CategoryBulkAssign(BaseModel):
    category: str = Field(
        min_length=1,
        max_length=128,
        description="Existing category name to assign to all provided transactions",
    )
    transaction_ids: list[UUID4] = Field(min_length=1, description="List of transaction UUIDs")
