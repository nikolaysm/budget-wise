"""Concrete DAO for the `Transaction` model built atop `BaseDAO` with helpers."""

from __future__ import annotations

from collections.abc import Iterable

from app.daos.base import BaseDAO
from app.models.transaction import Transaction


class TransactionDAO(BaseDAO[Transaction]):
    model = Transaction

    def assign_category(self, transaction_id, category_id) -> bool:  # noqa: ANN001
        tx = self.get(transaction_id)
        if tx is None:
            return False
        tx.category_id = category_id
        self.session.add(tx)
        self.session.commit()
        self.session.refresh(tx)
        return True

    def bulk_assign_category(self, transaction_ids: Iterable[str], category_id) -> int:  # noqa: ANN001
        updated = 0
        for tx_id in transaction_ids:
            tx = self.get(tx_id)
            if tx is None:
                continue
            tx.category_id = category_id
            self.session.add(tx)
            updated += 1
        if updated:
            self.session.commit()
        return updated

    def set_transaction_number(self, transaction_id: str, number: int) -> bool:
        """Set transaction_number if missing or different.

        Returns True if updated, False if tx not found.
        """
        tx = self.get(transaction_id)
        if tx is None:
            return False
        tx.transaction_number = number
        self.session.add(tx)
        self.session.commit()
        self.session.refresh(tx)
        return True
