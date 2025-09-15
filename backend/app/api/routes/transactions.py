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

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.deps import get_transaction_service
from app.core.config import get_settings
from app.models.transaction import Transaction
from app.schemas.pagination import PaginationIn, PaginationOut
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
    response_model=PaginationOut[Transaction],  # type: ignore[index]
    summary="List transactions (paginated)",
)
def list_transactions(
    *,
    params: PaginationIn = Depends(),  # offset & limit validated via model
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> PaginationOut[Transaction]:
    """Retrieve a paginated list of transactions wrapped in a pagination envelope."""
    # Fetch one extra to know if we have a next page
    rows, total = service.list_and_count(offset=params.offset, limit=params.limit + 1)
    items = rows[: params.limit]
    has_more = len(rows) > params.limit
    return PaginationOut[Transaction](  # type: ignore[call-arg]
        items=items,
        offset=params.offset,
        limit=params.limit,
        has_more=has_more,
        total=total,
    )


@router.get(
    "/{transaction_id}",
    response_model=Transaction,
    summary="Get a transaction by ID",
)
def read_transaction(
    *,
    transaction_id: int,
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> Transaction:
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
    return transaction
