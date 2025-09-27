"""
API routes for transaction ingestion and retrieval.

These endpoints allow clients to upload CSV or Excel files containing
transaction data. Each record is parsed into a `Transaction` model and
persisted to the database. Additional routes provide pagination for listing
transactions and retrieval by ID.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

from app.api.deps import get_transaction_service
from app.core.config import get_settings
from app.models.transaction import Transaction, TransactionOut
from app.schemas.pagination import PaginationIn, PaginationOut
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
        db (Session): Database session dependency.

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
    pagination: Annotated[PaginationIn, Query()],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> PaginationOut[Transaction]:
    """Retrieve a paginated list of transactions wrapped in a pagination envelope."""
    rows, total = service.list_and_count(
        offset=pagination.offset,
        limit=pagination.limit + 1,
        sort_by=pagination.sort_by,
        sort_dir=pagination.sort_dir,
    )
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
    "/{transaction_id}",
    response_model=TransactionOut,
    summary="Get a transaction by ID",
)
def read_transaction(
    *,
    transaction_id: str,  # UUID string
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionOut:
    """Retrieve a single transaction by its primary key.

    Args:
        transaction_id (int): ID of the transaction to retrieve.
        db (Session): Database session dependency.

    Returns:
        Transaction: The requested transaction.

    Raises:
        HTTPException: If the transaction does not exist.
    """
    transaction = service.get(transaction_id)
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
    transaction_id: str,
    payload: SetTransactionNumber,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionOut:
    """Assign a transaction number to an existing transaction (idempotent overwrite)."""
    try:
        tx = service.set_transaction_number(transaction_id, payload.number)
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
