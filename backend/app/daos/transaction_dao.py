"""Concrete DAO for the `Transaction` model built atop `BaseDAO`."""

from __future__ import annotations

from app.daos.base import BaseDAO
from app.models.transaction import Transaction


class TransactionDAO(BaseDAO[Transaction]):
    model = Transaction
