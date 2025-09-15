"""Concrete DAO for the `Account` model built atop `BaseDAO`."""

from __future__ import annotations

from typing import Any

from sqlmodel import select

from app.daos.base import BaseDAO
from app.models.account import Account


class AccountDAO(BaseDAO[Account]):
    """Data access object for `Account` entities."""

    model = Account

    def get_by_number(self, number: str) -> Account | None:
        stmt = select(Account).where(Account.number == number)
        return self.session.exec(stmt).first()

    def get_or_create(self, number: str, **extra: Any) -> Account:
        account = self.get_by_number(number)
        if account:
            return account
        # Only pass through known, simple fields; ignore unexpected keys for safety
        allowed_keys = {"bic", "bank_name", "currency", "user_id"}
        filtered: dict[str, Any] = {k: v for k, v in extra.items() if k in allowed_keys}
        account = Account(number=number, **filtered)
        return self.create(account)
