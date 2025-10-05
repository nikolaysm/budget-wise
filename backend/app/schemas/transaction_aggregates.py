"""Aggregation output schemas for transaction analytics endpoints."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class CategorySummaryItem(BaseModel):
    category: str | None
    count: int
    total_amount: Decimal


class CategorySummaryOut(BaseModel):
    items: list[CategorySummaryItem]
    date_from: str | None = None
    date_to: str | None = None
    total_amount: Decimal
    total_count: int
