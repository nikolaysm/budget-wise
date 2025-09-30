"""Category management API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.api.deps import get_category_service
from app.models.category import CategoryIn, CategoryOut
from app.schemas.category import CategoryAssign, CategoryBulkAssign
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("/", response_model=list[CategoryOut], summary="List categories")
def list_categories(
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> list[CategoryOut]:
    cats = service.list(limit=500)
    return [
        CategoryOut(
            id=c.id,
            name=c.name,
            slug=c.slug,
            expanded_phrase=c.expanded_phrase,
            aliases=c.aliases,
        )
        for c in cats
    ]


@router.get("/search", response_model=list[CategoryOut], summary="Search categories by name prefix")
def search_categories(
    q: str = Query(min_length=1, description="Search term (prefix or substring)"),
    limit: int = Query(default=20, ge=1, le=100),
    service: Annotated[CategoryService, Depends(get_category_service)] = None,  # type: ignore
) -> list[CategoryOut]:
    cats = service.search(q=q, limit=limit)  # type: ignore[arg-type]
    return [
        CategoryOut(
            id=c.id,
            name=c.name,
            slug=c.slug,
            expanded_phrase=c.expanded_phrase,
            aliases=c.aliases,
        )
        for c in cats
    ]


@router.post(
    "/",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category (idempotent by name)",
)
def create_category(
    payload: CategoryIn,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryOut:
    cat = service.create(
        payload.name,
        expanded_phrase=payload.expanded_phrase,
        aliases=payload.aliases,
    )
    return CategoryOut(
        id=cat.id,
        name=cat.name,
        slug=cat.slug,
        expanded_phrase=cat.expanded_phrase,
        aliases=cat.aliases,
    )


@router.put(
    "/{category_id}",
    response_model=CategoryOut,
    summary="Update a category (name / expanded_phrase / aliases)",
)
def update_category(
    category_id: Annotated[str, Path()],
    payload: CategoryIn,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryOut:
    try:
        # Rename first if name is changing
        cat = service.get(category_id)
        if not cat:
            raise ValueError
        if payload.name and payload.name != cat.name:
            cat = service.rename(category_id, payload.name)
        cat = service.update(
            category_id,
            expanded_phrase=payload.expanded_phrase,
            aliases=payload.aliases,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found") from None
    return CategoryOut(
        id=cat.id,
        name=cat.name,
        slug=cat.slug,
        expanded_phrase=cat.expanded_phrase,
        aliases=cat.aliases,
    )


@router.post(
    "/assign/{transaction_id}",
    summary="Assign an existing category to a transaction (no creation)",
    response_class=Response,
)
def assign_category(
    transaction_id: Annotated[str, Path(description="Transaction UUID")],
    payload: CategoryAssign,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> Response:
    try:
        service.assign_transaction_category(
            transaction_id=transaction_id, category_name=payload.category
        )
    except ValueError as exc:
        # differentiate missing category vs transaction
        detail = str(exc) or "Not found"
        raise HTTPException(status_code=404, detail=detail) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/assign/bulk",
    summary="Bulk assign an existing category to many transactions (no creation)",
)
def bulk_assign_category(
    payload: CategoryBulkAssign,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> dict[str, int]:
    try:
        count = service.bulk_assign(
            transaction_ids=payload.transaction_ids, category_name=payload.category
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return {"updated": count}
