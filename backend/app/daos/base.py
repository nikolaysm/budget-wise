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

    def _pk_name(self) -> Any:
        """Return the name of the primary key field for the model."""
        return inspect(self.model).primary_key[0].name

    def _default_order_by(self) -> Any:
        """Return default ordering for list() queries.

        Overridable in subclasses. Return one of:
        - a single column/expression (e.g., Model.id)
        - a tuple/list of columns/expressions (e.g., (desc(Model.date), Model.id))
        - None to apply no default ordering
        """
        return inspect(self.model).primary_key[0].name

    def get_queryset(self, *, offset: int = 0, limit: int = 100) -> SelectOfScalar[T]:
        stmt = select(self.model)
        order_by = self._default_order_by()
        if order_by is not None:
            stmt = stmt.order_by(order_by)
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

    def get(self, obj_id: Any) -> T | None:
        return self.session.get(self.model, obj_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[T]:
        stmt = self.get_queryset(offset=offset, limit=limit)
        return list(self.session.exec(stmt))

    def list_and_count(self, *, offset: int = 0, limit: int = 100) -> tuple[list[T], int]:
        stmt = self.get_queryset(offset=offset, limit=limit)
        stmt = stmt.add_columns(func.count(self._pk_name).over().label("total"))
        rows = self.session.exec(stmt)  # type: ignore[arg-type]
        import pdb

        pdb.set_trace()
        count = 0
        for row in rows:
            count = row.total  # type: ignore[attr-defined]
            break

        return rows, count
