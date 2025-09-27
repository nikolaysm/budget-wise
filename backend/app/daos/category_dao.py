"""DAO for Category model with extended helpers (search, uniqueness, lookups)."""

from __future__ import annotations

import re

from sqlmodel import func, select

from app.daos.base import BaseDAO
from app.models.category import Category


class CategoryDAO(BaseDAO[Category]):
    model = Category

    # Basic lookups -----------------------------------------------------
    def get_by_name(self, name: str) -> Category | None:
        stmt = select(Category).where(Category.name == name).limit(1)
        return self.session.exec(stmt).first()

    def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug).limit(1)
        return self.session.exec(stmt).first()

    # Search -------------------------------------------------------------
    def search(self, q: str, limit: int = 20) -> list[Category]:
        pattern = f"%{q.lower()}%"
        stmt = (
            select(Category)
            .where(func.lower(Category.name).like(pattern))
            .order_by(Category.name)
            .limit(limit)
        )
        return list(self.session.exec(stmt))

    # Creation with slug uniqueness -------------------------------------
    def _slug_for(self, name: str) -> str:
        base = name.strip().lower()
        base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
        return base or "category"

    def create_unique(self, name: str, *, commit: bool = True) -> Category:
        existing = self.get_by_name(name)
        if existing:
            return existing
        base_slug = self._slug_for(name)
        slug = base_slug
        suffix = 1
        while self.get_by_slug(slug) is not None:
            suffix += 1
            slug = f"{base_slug}-{suffix}"
        obj = Category(name=name, slug=slug)
        return self.create(obj, commit=commit, refresh=True)

    # Rename with slug update -------------------------------------------
    def rename(self, category_id, new_name: str) -> Category | None:  # noqa: ANN001
        cat = self.get(category_id)
        if not cat:
            return None
        if cat.name == new_name:
            return cat
        base_slug = self._slug_for(new_name)
        slug = base_slug
        suffix = 1
        while self.get_by_slug(slug) is not None and cat.slug != slug:
            suffix += 1
            slug = f"{base_slug}-{suffix}"
        cat.name = new_name
        cat.slug = slug
        self.session.add(cat)
        self.session.commit()
        self.session.refresh(cat)
        return cat
