"""Business logic for transactions (parsing & ingestion)."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd
from sqlmodel import Session

from app.daos.transaction_dao import TransactionDAO
from app.models.transaction import Transaction

EXPECTED_COLUMNS = [
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


@dataclass(slots=True)
class ParsedTransaction:
    """Lightweight representation before persistence (helps future validation)."""

    account: str
    booking_date: str | None
    statement_number: str | None
    transaction_number: str | None
    counterparty_account: str | None
    counterparty_name: str | None
    street_number: str | None
    postal_code_city: str | None
    transaction_type: str | None
    value_date: str | None
    amount: float
    currency: str | None
    bic: str | None
    country_code: str | None
    notes: str | None

    def to_model(self) -> Transaction:  # noqa: D401 - self explanatory
        return Transaction(
            account=self.account,
            booking_date=self.booking_date,
            statement_number=self.statement_number,
            transaction_number=self.transaction_number,
            counterparty_account=self.counterparty_account,
            counterparty_name=self.counterparty_name,
            street_number=self.street_number,
            postal_code_city=self.postal_code_city,
            transaction_type=self.transaction_type,
            value_date=self.value_date,
            amount=self.amount,
            currency=self.currency,
            bic=self.bic,
            country_code=self.country_code,
            notes=self.notes,
        )


class TransactionService:
    """High-level operations for transactions."""

    def __init__(self, dao: TransactionDAO, session: Session):  # session kept for future needs
        self.dao = dao
        self.session = session

    # --- Public API -----------------------------------------------------------
    def list(self, *, offset: int = 0, limit: int = 100) -> list[Transaction]:
        return self.dao.list(offset=offset, limit=limit)

    def get(self, tx_id: int) -> Transaction | None:
        return self.dao.get(tx_id)

    def ingest_file(self, *, filename: str, data: bytes) -> list[Transaction]:
        df = self._read_file(filename=filename, data=data)
        self._validate_columns(df)
        parsed = [self._row_to_parsed(row) for _, row in df.iterrows()]
        models = (p.to_model() for p in parsed)
        return self.dao.bulk_create(models)

    # --- Internal helpers -----------------------------------------------------
    def _read_file(self, *, filename: str, data: bytes) -> pd.DataFrame:
        if filename.endswith(".csv"):
            return pd.read_csv(io.BytesIO(data), sep=";")
        if filename.endswith((".xls", ".xlsx")):
            return pd.read_excel(io.BytesIO(data))
        raise ValueError("Unsupported file type: must be .csv, .xls, or .xlsx")

    def _validate_columns(self, df: pd.DataFrame) -> None:
        missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing expected columns: {missing}")

    @staticmethod
    def _val(value: Any):  # noqa: ANN001 - small internal helper
        import pandas as _pd  # local import to avoid polluting global namespace

        if value is None:
            return None
        try:
            if _pd.isna(value):  # type: ignore[arg-type]
                return None
        except Exception:  # pragma: no cover - defensive
            logging.debug("_val: isna check failed for value %r", value)
        return value

    def _row_to_parsed(self, row) -> ParsedTransaction:  # noqa: ANN001 - pandas row
        v = self._val
        return ParsedTransaction(
            account=str(v(row["Rekening"])) if v(row["Rekening"]) is not None else "",  # required
            booking_date=str(v(row["Boekingsdatum"])) if v(row["Boekingsdatum"]) else None,
            statement_number=str(v(row["Rekeninguittrekselnummer"]))
            if v(row["Rekeninguittrekselnummer"])
            else None,
            transaction_number=str(v(row["Transactienummer"]))
            if v(row["Transactienummer"])
            else None,
            counterparty_account=str(v(row["Rekening tegenpartij"]))
            if v(row["Rekening tegenpartij"])
            else None,
            counterparty_name=str(v(row["Naam tegenpartij bevat"]))
            if v(row["Naam tegenpartij bevat"])
            else None,
            street_number=str(v(row["Straat en nummer"])) if v(row["Straat en nummer"]) else None,
            postal_code_city=str(v(row["Postcode en plaats"]))
            if v(row["Postcode en plaats"])
            else None,
            transaction_type=str(v(row["Transactie"])) if v(row["Transactie"]) else None,
            value_date=str(v(row["Valutadatum"])) if v(row["Valutadatum"]) else None,
            amount=float(v(row["Bedrag"]) or 0.0),
            currency=str(v(row["Devies"])) if v(row["Devies"]) else None,
            bic=str(v(row["BIC"])) if v(row["BIC"]) else None,
            country_code=str(v(row["Landcode"])) if v(row["Landcode"]) else None,
            notes=str(v(row["Mededelingen"])) if v(row["Mededelingen"]) else None,
        )
