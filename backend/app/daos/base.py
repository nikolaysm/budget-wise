"""Generic BaseDAO providing common CRUD helpers.

Subclasses must define the `model` class attribute referencing the SQLModel
entity they manage.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, TypeVar

from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, func, select
from sqlmodel.sql.expression import SelectOfScalar

T = TypeVar("T", bound=SQLModel)


class BaseDAO(Generic[T]):
    """Base Data Access Object implementing common operations."""

    model: type[T]

    def __init__(self, session: Session):
        self.session = session

    @property
    def _pk_name(self) -> Any:
        """Return the name of the primary key field for the model."""
        return inspect(self.model).primary_key[0].name

    def _default_order_by(self) -> Any:
        """Default ORDER BY: primary key column (not its name)."""
        return self._pk_name

    def get_queryset(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        extra_columns: list[Any] | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> SelectOfScalar[T]:
        """Return a base query for listing objects, with optional pagination."""
        # columns can be additional selected expressions (e.g., count)
        columns = extra_columns or []
        stmt = select(self.model, *columns)
        # Determine ordering
        order_expr = None
        if sort_by:
            # Validate attribute exists
            if hasattr(self.model, sort_by):
                order_expr = getattr(self.model, sort_by)
                if sort_dir == "desc":  # default asc
                    order_expr = order_expr.desc()
            else:
                # Fallback to default order when invalid field supplied
                order_expr = self._default_order_by()
        else:
            order_expr = self._default_order_by()
        if order_expr is not None:
            stmt = stmt.order_by(order_expr)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        return stmt

    def create(self, obj: T, *, commit: bool = True, refresh: bool = True) -> T:
        self.session.add(obj)
        if commit:
            self.session.commit()
        if refresh:
            self.session.refresh(obj)
        return obj

    def bulk_create(
        self, objs: Iterable[T], *, commit: bool = True, refresh: bool = True
    ) -> list[T]:
        items = list(objs)
        if not items:
            return []
        self.session.add_all(items)
        if commit:
            self.session.commit()
        if refresh:
            for obj in items:
                self.session.refresh(obj)
        return items

    # Transaction helpers -------------------------------------------------
    def commit(self) -> None:
        """Commit the current database transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Rollback the current database transaction."""
        self.session.rollback()

    def get(self, obj_id: Any) -> T | None:
        return self.session.get(self.model, obj_id)

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[T]:
        stmt = self.get_queryset(offset=offset, limit=limit, sort_by=sort_by, sort_dir=sort_dir)
        return list(self.session.exec(stmt))

    def list_and_count(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> tuple[list[T], int]:
        total_col = func.count().over().label("_total_count")
        stmt = self.get_queryset(
            offset=offset,
            limit=limit,
            extra_columns=[total_col],
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        rows = self.session.exec(stmt).all()
        if not rows:
            return [], 0
        total = int(rows[0][1])  # type: ignore[index]
        items = [row[0] for row in rows]  # type: ignore[index]
        return items, total
