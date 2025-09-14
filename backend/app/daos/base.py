"""Generic BaseDAO providing common CRUD helpers.

Subclasses must define the `model` class attribute referencing the SQLModel
entity they manage.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseDAO(Generic[T]):
    """Base Data Access Object implementing common operations."""

    model: type[T]

    def __init__(self, session: Session):
        self.session = session

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

    def get(self, obj_id: int) -> T | None:
        return self.session.get(self.model, obj_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[T]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.session.exec(stmt))
