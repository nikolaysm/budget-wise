"""
API routes for transaction ingestion and retrieval.

These endpoints allow clients to upload CSV or Excel files containing
transaction data. Each record is parsed into a `Transaction` model and
persisted to the database. Additional routes provide pagination for listing
transactions and retrieval by ID.
"""

from __future__ import annotations

import io
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from app.api.deps import get_db
from app.crud.transaction import create_transaction, get_transaction, get_transactions
from app.models.transaction import Transaction


router = APIRouter()


@router.post(
    "/upload",
    response_model=List[Transaction],
    summary="Upload transactions from a CSV or Excel file",
    status_code=status.HTTP_201_CREATED,
)
async def upload_transactions(
    *, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> List[Transaction]:
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
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents), sep=";")
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise ValueError("Unsupported file type: must be .csv, .xls, or .xlsx")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing file: {e}",
        ) from e

    # Validate required columns
    expected_columns = [
        "Rekening",
        "Boekingsdatum",
        "Rekeninguittrekselnummer",
        "Transactienummer",
        "Rekening tegenpartij",
        "Naam tegenpartij bevat",
        "Straat en nummer",
        "Postcode en plaats",
        "Transactie",
        "Valutadatum",
        "Bedrag",
        "Devies",
        "BIC",
        "Landcode",
        "Mededelingen",
    ]
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing expected columns: {missing}",
        )

    transactions: List[Transaction] = []
    for _, row in df.iterrows():
        transaction = Transaction(
            account=str(row["Rekening"]),
            booking_date=str(row["Boekingsdatum"]),
            statement_number=str(row["Rekeninguittrekselnummer"])
            if not pd.isna(row["Rekeninguittrekselnummer"])
            else None,
            transaction_number=str(row["Transactienummer"])
            if not pd.isna(row["Transactienummer"])
            else None,
            counterparty_account=str(row["Rekening tegenpartij"])
            if not pd.isna(row["Rekening tegenpartij"])
            else None,
            counterparty_name=str(row["Naam tegenpartij bevat"])
            if not pd.isna(row["Naam tegenpartij bevat"])
            else None,
            street_number=str(row["Straat en nummer"])
            if not pd.isna(row["Straat en nummer"])
            else None,
            postal_code_city=str(row["Postcode en plaats"])
            if not pd.isna(row["Postcode en plaats"])
            else None,
            transaction_type=str(row["Transactie"])
            if not pd.isna(row["Transactie"])
            else None,
            value_date=str(row["Valutadatum"])
            if not pd.isna(row["Valutadatum"])
            else None,
            amount=float(row["Bedrag"]),
            currency=str(row["Devies"])
            if not pd.isna(row["Devies"])
            else None,
            bic=str(row["BIC"])
            if not pd.isna(row["BIC"])
            else None,
            country_code=str(row["Landcode"])
            if not pd.isna(row["Landcode"])
            else None,
            notes=str(row["Mededelingen"])
            if not pd.isna(row["Mededelingen"])
            else None,
        )
        saved = create_transaction(db, transaction=transaction)
        transactions.append(saved)
    return transactions


@router.get(
    "/",
    response_model=List[Transaction],
    summary="List transactions",
)
def list_transactions(
    *,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[Transaction]:
    """Retrieve a paginated list of transactions.

    Args:
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.
        db (Session): Database session dependency.

    Returns:
        List[Transaction]: A list of transactions.
    """
    return get_transactions(db, skip=skip, limit=limit)


@router.get(
    "/{transaction_id}",
    response_model=Transaction,
    summary="Get a transaction by ID",
)
def read_transaction(
    *,
    transaction_id: int,
    db: Session = Depends(get_db),
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
    transaction = get_transaction(db, transaction_id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction