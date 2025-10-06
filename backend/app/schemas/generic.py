"""Generic schemas for filtering."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel


class BaseFilters(BaseModel, ABC):
    """Abstract base class for filter schemas that produce a Django-ish filter dict."""

    #: Optional mapping: public field -> backend key (e.g., "amount_gte" -> "amount__gte")
    FIELD_OPS: ClassVar[dict[str, str]] = {}
    #: Whether to drop empty strings as well as None
    EXCLUDE_EMPTY: ClassVar[bool] = True

    def _base_dump(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        if self.EXCLUDE_EMPTY:
            data = {k: v for k, v in data.items() if v != ""}
        # remap keys via FIELD_OPS
        out: dict[str, Any] = {}
        for k, v in data.items():
            out[self.FIELD_OPS.get(k, k)] = v
        return out

    @abstractmethod
    def to_filter_dict(self) -> dict[str, Any]:
        """Convert to a dict suitable for apply_filters(). Must be implemented by subclasses."""
        raise NotImplementedError
