"""
API routes for transaction ingestion and retrieval.

These endpoints allow clients to upload CSV or Excel files containing
transaction data. Each record is parsed into a `Transaction` model and
persisted to the database. Additional routes provide pagination for listing
transactions and retrieval by ID.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

from app.api.deps import get_transaction_service
from app.core.config import get_settings
from app.models.transaction import Transaction, TransactionOut
from app.schemas import (
    CategorySummaryOut,
    PaginationIn,
    PaginationOut,
    SortParams,
    TransactionFilters,
)
from app.schemas.transaction import SetTransactionNumber
from app.services.transaction_service import TransactionService

logger = logging.getLogger(get_settings().app_logger_name)

router = APIRouter()


@router.post(
    "/upload",
    response_model=list[Transaction],
    summary="Upload transactions from a CSV or Excel file",
    status_code=status.HTTP_201_CREATED,
)
async def upload_transactions(
    *,
    file: UploadFile,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> list[Transaction]:
    """Parse the uploaded file and persist each transaction.

    The file must contain a header row with expected column names. Supported
    formats are `.csv` (semicolon‑delimited) and Excel (`.xls`/`.xlsx`).

    Args:
        file (UploadFile): The uploaded file containing transactions.

    Returns:
        List[Transaction]: A list of persisted transactions.

    Raises:
        HTTPException: If the file format is unsupported or parsing fails.
    """
    filename = file.filename or ""
    contents = await file.read()
    try:
        return service.ingest_file(filename=filename, data=contents)
    except Exception as e:  # broad to convert into HTTP error
        logger.error("Error processing uploaded file %s: %s", filename, e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing upload: {e}",
        ) from e


@router.get(
    "/",
    response_model=PaginationOut[TransactionOut],
    summary="List transactions (paginated)",
)
async def list_transactions(
    pagination: Annotated[PaginationIn, Depends()],
    filters: Annotated[TransactionFilters, Depends()],
    sorting: Annotated[SortParams, Depends()],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    # pagination: Annotated[PaginationIn, Query()],
    # filters: Annotated[TransactionFilters, Query()],
) -> PaginationOut[TransactionOut]:
    """Retrieve a paginated list of transactions wrapped in a pagination envelope."""
    rows, total = service.list_and_count(pagination=pagination, sorting=sorting, filters=filters)
    items = rows[: pagination.limit]
    has_more = len(rows) > pagination.limit
    # Map to read schema adding category_name
    read_items: list[TransactionOut] = []
    for tx in items:
        cat = getattr(tx, "category", None)
        cat_name = getattr(cat, "name", None) if cat is not None else None
        # Build TransactionOut manually; ensure id & category
        read_items.append(
            TransactionOut(
                id=tx.id,
                account=tx.account,
                booking_date=tx.booking_date,
                statement_number=tx.statement_number,
                transaction_number=tx.transaction_number,
                counterparty_account=tx.counterparty_account,
                counterparty_name=tx.counterparty_name,
                street_number=tx.street_number,
                postal_code_city=tx.postal_code_city,
                transaction_type=tx.transaction_type,
                value_date=tx.value_date,
                amount=tx.amount,
                currency=tx.currency,
                bic=tx.bic,
                country_code=tx.country_code,
                notes=tx.notes,
                category=cat_name,
                category_id=tx.category_id,
                account_id=tx.account_id,
            )
        )
    return PaginationOut[TransactionOut](
        items=read_items,  # type: ignore[arg-type]
        offset=pagination.offset,
        limit=pagination.limit,
        has_more=has_more,
        total=total,
    )


@router.get(
    "/suggest-categories",
    summary="Suggest categories for uncategorized transactions (batch)",
)
def suggest_categories(
    *,
    limit: int = Query(25, ge=1, le=200),
    threshold: float = Query(0.4, ge=0, le=1),
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> list[dict]:
    return service.bulk_suggest_categories(limit=limit, threshold=threshold)


@router.get(
    "/stats",
    summary="Get transaction categorization stats",
)
def transaction_stats(
    *, service: Annotated[TransactionService, Depends(get_transaction_service)]
) -> dict[str, int]:
    """Return counts of transactions with and without categories."""
    return service.categorization_stats()


@router.get(
    "/category-summary",
    response_model=CategorySummaryOut,
    summary="Aggregate transactions by category (with optional date range)",
)
def transaction_category_summary(
    *,
    date_from: date | None = Query(None, description="Inclusive start booking_date"),
    date_to: date | None = Query(None, description="Inclusive end booking_date"),
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> CategorySummaryOut:
    """Return aggregated totals grouped by category as an envelope with totals."""
    return service.category_summary(date_from=date_from, date_to=date_to)


@router.get(
    "/{transaction_id}",
    response_model=TransactionOut,
    summary="Get a transaction by ID",
)
def read_transaction(
    *,
    transaction_id: UUID,  # UUID path param
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionOut:
    """Retrieve a single transaction by its primary key.

    FastAPI will only match this route if the path segment is a valid UUID,
    preventing accidental capture of static subpaths like 'suggest-categories'.
    """
    transaction = service.get(str(transaction_id))
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    cat = getattr(transaction, "category", None)
    cat_name = getattr(cat, "name", None) if cat is not None else None
    return TransactionOut(
        id=transaction.id,
        account=transaction.account,
        booking_date=transaction.booking_date,
        statement_number=transaction.statement_number,
        transaction_number=transaction.transaction_number,
        counterparty_account=transaction.counterparty_account,
        counterparty_name=transaction.counterparty_name,
        street_number=transaction.street_number,
        postal_code_city=transaction.postal_code_city,
        transaction_type=transaction.transaction_type,
        value_date=transaction.value_date,
        amount=transaction.amount,
        currency=transaction.currency,
        bic=transaction.bic,
        country_code=transaction.country_code,
        notes=transaction.notes,
        category=cat_name,
        category_id=transaction.category_id,
        account_id=transaction.account_id,
    )


@router.patch(
    "/{transaction_id}/set-number",
    response_model=TransactionOut,
    summary="Set a transaction number on a transaction",
)
def set_transaction_number(
    *,
    transaction_id: UUID,
    payload: SetTransactionNumber,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionOut:
    """Assign a transaction number to an existing transaction (idempotent overwrite)."""
    try:
        tx = service.set_transaction_number(str(transaction_id), payload.number)
    except ValueError:
        raise HTTPException(status_code=404, detail="Transaction not found") from None
    cat = getattr(tx, "category", None)
    cat_name = getattr(cat, "name", None) if cat is not None else None
    return TransactionOut(
        id=tx.id,
        account=tx.account,
        booking_date=tx.booking_date,
        statement_number=tx.statement_number,
        transaction_number=tx.transaction_number,
        counterparty_account=tx.counterparty_account,
        counterparty_name=tx.counterparty_name,
        street_number=tx.street_number,
        postal_code_city=tx.postal_code_city,
        transaction_type=tx.transaction_type,
        value_date=tx.value_date,
        amount=tx.amount,
        currency=tx.currency,
        bic=tx.bic,
        country_code=tx.country_code,
        notes=tx.notes,
        category=cat_name,
        category_id=tx.category_id,
        account_id=tx.account_id,
    )


@router.get(
    "/{transaction_id}/suggest-category",
    summary="Suggest a category for a single transaction",
)
def suggest_transaction_category(
    *,
    transaction_id: UUID,
    threshold: float = Query(0.4, ge=0, le=1),
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> dict:
    try:
        suggested, score, reason, counterparty_name = service.suggest_category_for(
            str(transaction_id), threshold=threshold
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Transaction not found") from None
    return {
        "id": str(transaction_id),
        "suggested": suggested,
        "score": score,
        "reason": reason,
        "counterparty_name": counterparty_name,
    }
