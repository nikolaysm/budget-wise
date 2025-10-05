"""Concrete DAO for the `Transaction` model built atop `BaseDAO` with helpers."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import date
from uuid import UUID

from sqlalchemy import func
from sqlmodel import select

from app.core.config import settings
from app.daos.base import BaseDAO
from app.models.category import Category
from app.models.transaction import Transaction

logger = logging.getLogger(settings.app_logger_name)


class TransactionDAO(BaseDAO[Transaction]):
    model = Transaction

    def assign_category(
        self, transaction_id: UUID, category_id: UUID, *, commit: bool = True
    ) -> bool:
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

    def bulk_assign_category(self, transaction_ids: Iterable[UUID], category_id) -> int:  # noqa: ANN001
        updated = 0
        for tx_id in transaction_ids:
            tx = self.get(tx_id)
            if tx is None:
                continue
            # Skip if already assigned (cheap optimization)
            if tx.category_id == category_id:
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

    # --- Aggregates ---------------------------------------------------------
    def count_categorization_stats(self) -> dict[str, int]:
        """Return counts of transactions grouped by presence of category.

        Returns a dict with keys: total, with_category, without_category.
        """

        # total count
        total = self.session.exec(select(func.count()).select_from(self.model)).one()

        # with category
        with_cat = self.session.exec(
            select(func.count()).select_from(self.model).where(self.model.category_id.is_not(None))  # type: ignore[attr-defined]
        ).one()

        total_int = int(total)
        with_int = int(with_cat)
        return {
            "total": total_int,
            "with_category": with_int,
            "without_category": total_int - with_int,
        }

    def category_summary(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, object]]:
        """Aggregate transactions by category with optional booking_date range.

        Returns list of dicts: {category: str|None, count: int, total_amount: Decimal}
        Uncategorized transactions will have category = None.
        """
        tx = self.model
        stmt = (
            select(
                Category.name,  # may be NULL for uncategorized due to outer join
                func.count(),  # count rows
                func.coalesce(func.sum(tx.amount), 0),
            )
            .select_from(tx)
            .join(Category, tx.category_id == Category.id, isouter=True)  # type: ignore[arg-type]
        )
        if date_from is not None:
            stmt = stmt.where(tx.booking_date >= date_from)  # type: ignore[operator]
        if date_to is not None:
            stmt = stmt.where(tx.booking_date <= date_to)  # type: ignore[operator]
        stmt = stmt.group_by(Category.name).order_by(func.coalesce(func.sum(tx.amount), 0).desc())
        rows = self.session.exec(stmt).all()
        results: list[dict[str, object]] = []
        for category_name, count_val, total_amount in rows:  # type: ignore[misc]
            results.append(
                {
                    "category": category_name,
                    "count": int(count_val),
                    "total_amount": total_amount,
                }
            )
        return results
