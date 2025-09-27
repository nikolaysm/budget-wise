"""Business logic for categories (delegates all DB work to DAOs)."""

from __future__ import annotations

from collections.abc import Iterable

from sqlmodel import Session

from app.daos.category_dao import CategoryDAO
from app.daos.transaction_dao import TransactionDAO
from app.models.category import Category


class CategoryService:
    def __init__(
        self, category_dao: CategoryDAO, transaction_dao: TransactionDAO, session: Session
    ):
        self.category_dao = category_dao
        self.transaction_dao = transaction_dao
        self.session = session

    # Category CRUD ---------------------------------------------------------
    def list(self, *, offset: int = 0, limit: int = 100) -> list[Category]:
        return self.category_dao.list(offset=offset, limit=limit)

    def search(self, *, q: str, limit: int = 20) -> list[Category]:
        return self.category_dao.search(q, limit)

    def get(self, category_id) -> Category | None:  # UUID auto-handled  # noqa: ANN001
        return self.category_dao.get(category_id)

    def get_by_name(self, name: str) -> Category | None:  # noqa: D401
        return self.category_dao.get_by_name(name)

    def create(self, name: str) -> Category:
        return self.category_dao.create_unique(name)

    def rename(self, category_id, new_name: str) -> Category:
        cat = self.category_dao.rename(category_id, new_name)
        if not cat:
            raise ValueError("Category not found")
        return cat

    def bulk_create(self, names: Iterable[str]) -> list[Category]:
        return [self.create(n) for n in names]

    # (Internal slug helpers removed; handled by DAO)

    # Assign category to a transaction --------------------------------------
    def assign_transaction_category(self, *, transaction_id, category_name: str) -> None:
        category = self.get_by_name(category_name)
        if category is None:
            raise ValueError("Category not found")
        ok = self.transaction_dao.assign_category(transaction_id, category.id)
        if not ok:
            raise ValueError("Transaction not found")

    def bulk_assign(self, *, transaction_ids: list[str], category_name: str) -> int:
        category = self.get_by_name(category_name)
        if category is None:
            raise ValueError("Category not found")
        return self.transaction_dao.bulk_assign_category(transaction_ids, category.id)
