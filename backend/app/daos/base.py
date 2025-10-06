"""Generic BaseDAO providing common CRUD helpers + dynamic filtering/sorting.

Features:
    * CRUD helpers (create, bulk_create, get)
    * Offset pagination support
    * Dynamic filtering & ordering powered by :class:`QueryBuilder`
        - Django‑style operators (``field__gte=`` / ``field__ilike=`` / ``rel__name__exact=``)
        - Relationship traversal with automatic (outer) joins
        - Multi-field ordering (``amount:desc`` / ``-booking_date`` / ``category__name:asc``)
    * Single-query list_and_count using window function counting

Subclasses only need to set ``model``. Optionally override:
    * ``default_sorts`` – to change default ordering when client provides none.
    * ``default_options`` – to add eager loading options.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import SelectOfScalar

from app.db.generic_filters import QueryBuilder
from app.schemas import BaseFilters, PaginationIn, SortParams

T = TypeVar("T", bound=SQLModel)


class BaseDAO(Generic[T]):
    """Base Data Access Object implementing common operations."""

    model: type[T]
    _qd: QueryBuilder[T] | None = None

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Query builder + base select
    # ------------------------------------------------------------------
    def base_select(self) -> SelectOfScalar[T]:  # legacy (kept for backward compat)
        """Starting point for SELECTs (override to inject joins/options).

        Prefer using the integrated QueryBuilder via ``self.qb`` for new code.
        """
        return select(self.model)

    @property
    def qb(self) -> QueryBuilder[T]:  # lazy init so subclasses can override flags
        if self._qd is None:
            # outerjoin to preserve parent rows even when related path filters used
            self._qd = QueryBuilder(self.model, use_outerjoin=True)
        return self._qd

    def default_sorts(self) -> list[str]:
        """Default ordering (override per model)."""
        pk = inspect(self.model).primary_key[0]
        return [f"{pk.name}:asc"]

    def default_options(self):
        """SQLAlchemy loader options (e.g., joinedload relations)."""
        return ()

    def create(self, obj: T, *, commit: bool = True, refresh: bool = True) -> T:
        self.session.add(obj)
        if commit:
            # Commit makes the instance persistent and safe to refresh
            self.session.commit()
        else:
            # Ensure PKs / defaults are populated so caller can use the object before commit
            # (flush does not commit the transaction)
            if refresh:
                self.session.flush()
        if refresh:
            # Refresh after commit or flush so attributes (defaults, triggers) are loaded
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
        else:
            if refresh:
                self.session.flush()
        if refresh:
            for obj in items:
                self.session.refresh(obj)
        return items

    def get(self, obj_id: Any) -> T | None:
        return self.session.get(self.model, obj_id)

    def list(
        self,
        *,
        pagination: PaginationIn,
        sorting: SortParams,
        filters: BaseFilters | None = None,
    ) -> list[T]:
        """List items with dynamic filters + ordering (no total COUNT).

        Parameters:
            pagination: ``PaginationIn`` instance (offset, limit)
            sorting: ``SortParams`` (converted to list[str] via ``to_sorts``)
            filters: Optional filters object implementing ``to_filter_dict``
        """
        sorts = sorting.to_sorts(default=self.default_sorts())
        filt_dict = filters.to_filter_dict() if filters is not None else {}

        stmt = self.qb.select_scalar().options(*self.default_options())
        stmt = self.qb.apply_filters(stmt, filt_dict)
        stmt = self.qb.apply_ordering(stmt, sorts)
        if pagination.offset:
            stmt = stmt.offset(pagination.offset)
        if pagination.limit:
            stmt = stmt.limit(pagination.limit)
        results = self.session.exec(stmt)
        return cast(list[T], results)

    def list_and_count(
        self,
        *,
        pagination: PaginationIn,
        sorting: SortParams,
        filters: Any = None,
    ) -> tuple[list[T], int]:
        """Return (items, total) in a single window-function query.

        Uses ``QueryBuilder.select_items_and_total`` which adds a ``_total_count`` column.
        """
        sorts = sorting.to_sorts(default=self.default_sorts())
        filt_dict = filters.to_filter_dict() if filters is not None else {}
        stmt = self.qb.select_items_and_total(
            filters=filt_dict,
            sorts=sorts,
            offset=pagination.offset,
            limit=pagination.limit,
        ).options(*self.default_options())
        # Get a Result object from the execution of the statement.
        result = self.session.exec(stmt)
        rows = result.all()
        if not rows:
            return [], 0
        # Rows are tuples: (model_instance, total_count from window function)
        items = [cast(T, r[0]) for r in rows]
        total = int(rows[0][1])
        return items, total

    # ------------------------------------------------------------------
    # Explicit transaction helpers (optional higher-level use)
    # ------------------------------------------------------------------
    def commit(self) -> None:  # pragma: no cover - trivial wrapper
        self.session.commit()

    def rollback(self) -> None:  # pragma: no cover - trivial wrapper
        self.session.rollback()
