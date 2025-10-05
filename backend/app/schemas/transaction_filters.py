"""Transaction filters schema."""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from .generic import BaseFilters


class TransactionFilters(BaseFilters):
    category_id: UUID | None = None
    has_category: bool | None = None
    account: str | None = None
    amount_gte: Decimal | None = None
    amount_lte: Decimal | None = None
    booking_date_gte: date | None = None
    booking_date_lte: date | None = None
    notes_ilike: str | None = None
    counterparty_name_ilike: str | None = None
    counterparty_name_icontains: str | None = None
    transaction_type_ilike: str | None = None

    FIELD_OPS = {
        "amount_gte": "amount__gte",
        "amount_lte": "amount__lte",
        "booking_date_gte": "booking_date__gte",
        "booking_date_lte": "booking_date__lte",
        "notes_ilike": "notes__ilike",
        "counterparty_name_ilike": "counterparty_name__ilike",
        "transaction_type_ilike": "transaction_type__ilike",
        "counterparty_name_icontains": "counterparty_name__icontains",
    }

    def to_filter_dict(self) -> dict[str, Any]:
        out = self._base_dump()
        # map has_category into an isnull check:
        has = out.pop("has_category", None)
        if has is True:
            out["category_id__isnull"] = False
        elif has is False:
            out["category_id__isnull"] = True
        return out
