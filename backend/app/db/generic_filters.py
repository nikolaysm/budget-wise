from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import false, func, inspect, true
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import SQLModel
from sqlmodel import select as sm_select
from sqlmodel.sql.expression import Select as SMSelect
from sqlmodel.sql.expression import SelectOfScalar

# --- type vars / aliases ----------------------------------------------------

SelectT = TypeVar("SelectT", SMSelect, SelectOfScalar)  # preserve select type through helpers
ModelT = TypeVar("ModelT", bound=SQLModel)
Columnish = InstrumentedAttribute | ColumnElement[Any]  # both support ColumnOperators


# --- operators (ColumnOperators) --------------------------------------------


def _op_exact(c: Columnish, v):
    return c == v


def _op_ne(c: Columnish, v):
    return c != v


def _op_gt(c: Columnish, v):
    return c > v


def _op_gte(c: Columnish, v):
    return c >= v


def _op_lt(c: Columnish, v):
    return c < v


def _op_lte(c: Columnish, v):
    return c <= v


def _as_list(v: Iterable | None) -> list | None:
    if v is None:
        return None
    return list(v)


def _op_in(c: Columnish, v: Iterable | None):
    vals = _as_list(v)
    if vals is None:
        # No values provided -> no filter condition (always true)
        return true()
    if len(vals) == 0:
        # Empty IN list is always false
        return false()
    return c.in_(vals)


def _op_notin(c: Columnish, v: Iterable | None):
    vals = _as_list(v)
    if vals is None:
        # No values provided -> no filter condition (always true)
        return true()
    if len(vals) == 0:
        # NOT IN () with empty list is always true
        return true()
    return ~c.in_(vals)


def _op_range(c: Columnish, v: Sequence[Any]):
    lo, hi = v
    return c.between(lo, hi)


def _op_contains(c: Columnish, v: Any):
    return c.contains(v)


def _op_like(c: Columnish, v: str):
    return c.like(v)


def _op_notlike(c: Columnish, v: str):
    return ~c.like(v)


def _op_ilike(c: Columnish, v: str):
    return c.ilike(v)


def _op_notilike(c: Columnish, v: str):
    return ~c.ilike(v)


def _op_startswith(c: Columnish, v: str):
    return c.startswith(v)


def _op_endswith(c: Columnish, v: str):
    return c.endswith(v)


def _op_isnull(c: Columnish, v: bool):
    return c.is_(None) if v else c.is_not(None)


OPERATORS: dict[str, Callable[[Columnish, Any], Any]] = {
    "exact": _op_exact,
    "ne": _op_ne,
    "gt": _op_gt,
    "gte": _op_gte,
    "lt": _op_lt,
    "lte": _op_lte,
    "in": _op_in,
    "notin": _op_notin,
    "range": _op_range,
    "contains": _op_contains,
    "like": _op_like,
    "notlike": _op_notlike,
    "ilike": _op_ilike,
    "notilike": _op_notilike,
    "startswith": _op_startswith,
    "endswith": _op_endswith,
    "isnull": _op_isnull,
}


# --- core class -------------------------------------------------------------


class QueryBuilder(Generic[ModelT]):
    """
    Generic SQLAlchemy 2.x filtering & sorting for a given SQLModel.
    Supports:
      - Django-ish filters: {"amount__gte": 0, "notes__ilike": "rent"}
      - Nested paths + auto-join: {"category__name__ilike": "grocer"}
      - Sort specs: ["-booking_date", "amount:asc", "category__name:desc"]
      - One-query items + total via window count()
    """

    def __init__(self, model: type[ModelT], *, use_outerjoin: bool = False):
        self.model = model
        self.use_outerjoin = use_outerjoin

    def _is_relationship(self, attr: Any) -> bool:
        return (
            isinstance(attr, InstrumentedAttribute)
            and hasattr(attr, "property")
            and hasattr(attr.property, "direction")
        )

    def _resolve_path(
        self,
        stmt: SelectT,
        tokens: list[str],
        join_cache: dict[tuple[str, ...], Any],
    ) -> tuple[SelectT, Columnish]:
        """
        Walk a path like ["category", "name"]; auto-join with aliased() as needed.
        Returns (stmt, column).
        """
        current: Any = self.model
        path: list[str] = []
        for tok in tokens:
            path.append(tok)
            attr = getattr(current, tok)
            if self._is_relationship(attr):
                key = tuple(path)
                alias = join_cache.get(key)
                if alias is None:
                    target = attr.property.mapper.class_
                    alias = aliased(target)
                    stmt = (
                        stmt.outerjoin(alias, attr)
                        if self.use_outerjoin
                        else stmt.join(alias, attr)
                    )  # type: ignore[attr-defined]
                    join_cache[key] = alias
                current = alias
            else:
                return stmt, getattr(current, tok)

        # path ended on a relationship; fall back to that entity's PK
        pk = inspect(current).primary_key[0]
        pk_key = getattr(pk, "key", None) or pk.name
        return stmt, getattr(current, pk_key)

    def apply_filters(self, stmt: SelectT, filters: Mapping[str, Any] | None) -> SelectT:
        if not filters:
            return stmt
        join_cache: dict[tuple[str, ...], Any] = {}
        wheres: list[Any] = []
        for key, value in filters.items():
            if value is None:
                continue
            tokens = key.split("__")
            op_name = "exact"
            if tokens[-1] in OPERATORS:
                op_name = tokens.pop()
            stmt, col = self._resolve_path(stmt, tokens, join_cache)
            expr = OPERATORS[op_name](col, value)
            wheres.append(expr)
        return stmt.where(*wheres) if wheres else stmt  # type: ignore[attr-defined]

    def apply_ordering(self, stmt: SelectT, sorts: Sequence[str] | None) -> SelectT:
        if not sorts:
            return stmt
        join_cache: dict[tuple[str, ...], Any] = {}
        order_exprs: list[Any] = []
        for spec in sorts:
            if ":" in spec:
                field, direction = spec.split(":", 1)
                desc = direction.lower() == "desc"
            else:
                desc = spec.startswith("-")
                field = spec[1:] if spec[:1] in "+-" else spec
            tokens = field.split("__")
            stmt, col = self._resolve_path(stmt, tokens, join_cache)
            order_exprs.append(col.desc() if desc else col.asc())
        return stmt.order_by(*order_exprs)  # type: ignore[attr-defined]

    # ---- builders ----

    def select_scalar(self) -> SelectOfScalar[ModelT]:
        """Select that returns scalars (model instances)."""
        return sm_select(self.model)

    def select_items_and_total(
        self,
        *,
        filters: Mapping[str, Any] | None = None,
        sorts: Sequence[str] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> SMSelect[tuple[ModelT, int]]:
        """Select(model, _total_count) using a window count()."""
        total_col = func.count().over().label("_total_count")
        # When selecting multiple entities/columns, sqlmodel.select returns a core SA Select
        stmt = cast(SMSelect[tuple[ModelT, int]], sm_select(self.model, total_col))
        stmt = self.apply_filters(stmt, filters)
        stmt = self.apply_ordering(stmt, sorts)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        return stmt

    # ---- small utilities ----

    @staticmethod
    def normalize_sorts(
        sort_by: str | None, sort_dir: str | None, *, default: Sequence[str] | None = None
    ) -> list[str]:
        if not sort_by:
            return list(default or [])
        direction = (sort_dir or "asc").lower()
        return [f"{sort_by}:{direction}"]

    @staticmethod
    def prune_nones(d: Mapping[str, Any] | None) -> dict[str, Any]:
        if not d:
            return {}
        return {k: v for k, v in d.items() if v not in (None, "")}
