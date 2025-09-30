"""Concrete DAO for the `Transaction` model built atop `BaseDAO` with helpers."""

from __future__ import annotations

from collections.abc import Iterable

from app.daos.base import BaseDAO
from app.models.transaction import Transaction


class TransactionDAO(BaseDAO[Transaction]):
    model = Transaction

    def get_queryset(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        extra_columns: list | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        category_id=None,  # UUID | None but keep loose for forward ref
        has_category: bool | None = None,
    ):
        """Return a selectable query with optional category filtering.

        Parameters:
            offset / limit / extra_columns / sort_by / sort_dir: same as BaseDAO.get_queryset
            category_id: if provided, restricts to rows with this category_id
            has_category:
                * True  -> only rows where category_id IS NOT NULL
                * False -> only rows where category_id IS NULL
                * None  -> no nullability filter

        Notes:
            - Both category_id and has_category can be combined; category_id takes precedence.
            - This override keeps backward compatibility: callers that do not pass the new
              parameters get the original behavior.
        """
        stmt = super().get_queryset(
            offset=offset,
            limit=limit,
            extra_columns=extra_columns,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        if has_category is True:
            stmt = stmt.where(self.model.category_id != None)  # noqa: E711
        elif has_category is False:
            stmt = stmt.where(self.model.category_id == None)  # noqa: E711
        if category_id is not None:
            stmt = stmt.where(self.model.category_id == category_id)
        return stmt

    def assign_category(self, transaction_id, category_id, *, commit: bool = True) -> bool:  # noqa: ANN001
        """Assign a category to a transaction.

        Parameters:
            transaction_id: The id of the transaction.
            category_id: The id of the category.
            commit: When False, changes are staged but not committed (caller batches commits).

        Returns True if assignment occurred; False if transaction not found.
        """
        tx = self.get(transaction_id)
        if tx is None:
            return False
        # Skip if already assigned to same category
        if tx.category_id == category_id:
            return True
        tx.category_id = category_id
        self.session.add(tx)
        if commit:
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
