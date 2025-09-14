"""
API routes for transaction ingestion and retrieval.

These endpoints allow clients to upload CSV or Excel files containing
transaction data. Each record is parsed into a `Transaction` model and
persisted to the database. Additional routes provide pagination for listing
transactions and retrieval by ID.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.deps import get_transaction_service
from app.models.transaction import Transaction
from app.services.transaction_service import TransactionService

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
    service: TransactionService = Depends(get_transaction_service),  # noqa: B008
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing upload: {e}",
        ) from e


@router.get(
    "/",
    response_model=list[Transaction],
    summary="List transactions",
)
def list_transactions(
    *,
    offset: int = 0,
    limit: int = 100,
    service: TransactionService = Depends(get_transaction_service),  # noqa: B008
) -> list[Transaction]:
    """Retrieve a paginated list of transactions.

    Args:
        offset (int, optional): Number of records to offset. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.
        db (Session): Database session dependency.

    Returns:
        List[Transaction]: A list of transactions.
    """
    return service.list(offset=offset, limit=limit)


@router.get(
    "/{transaction_id}",
    response_model=Transaction,
    summary="Get a transaction by ID",
)
def read_transaction(
    *,
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),  # noqa: B008
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
