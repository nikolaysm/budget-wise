"""API request body schemas for Transaction operations not covered by model I/O.

Currently includes small mutation payloads.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SetTransactionNumber(BaseModel):
    number: int = Field(ge=1, description="Transaction number to set")
