"""Business logic for transactions (parsing & ingestion)."""

from __future__ import annotations

import io
import logging

import pandas as pd
from pydantic import ValidationError
from sqlmodel import Session

from app.core.config import get_settings
from app.daos.account_dao import AccountDAO
from app.daos.transaction_dao import TransactionDAO
from app.models.account import Account
from app.models.transaction import Transaction, TransactionIn

logger = logging.getLogger(get_settings().app_logger_name)

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


class TransactionService:
    """High-level operations for transactions."""

    def __init__(
        self, dao: TransactionDAO, account_dao: AccountDAO, session: Session
    ):  # session kept for future needs
        self.dao = dao
        self.session = session
        self.account_dao = account_dao

    # --- Public API -----------------------------------------------------------
    def list(self, *, offset: int = 0, limit: int = 100) -> list[Transaction]:
        return self.dao.list(offset=offset, limit=limit)

    def list_and_count(self, *, offset: int = 0, limit: int = 100) -> tuple[list[Transaction], int]:
        return self.dao.list_and_count(offset=offset, limit=limit)

    def get(self, tx_id: int) -> Transaction | None:
        return self.dao.get(tx_id)

    def ingest_file(self, *, filename: str, data: bytes) -> list[Transaction]:
        """Parse the uploaded file and persist each transaction."""
        table_data = self._extract_single_table(data)
        df = self._read_file(filename=filename, data=table_data)
        self._validate_columns(df)
        # Ensure Account rows exist for each unique account number prior to transaction insertion
        account_map: dict[str, Account] = {}
        for acc_number_obj in df["Rekening"].unique():  # type: ignore[index]
            if acc_number_obj is None:
                continue
            acc_number = str(acc_number_obj)
            account_map[acc_number] = self.account_dao.get_or_create(number=acc_number)

        models = (self._row_to_parsed(row, account_map) for _, row in df.iterrows())
        return self.dao.bulk_create(models)

    # --- Internal helpers -----------------------------------------------------
    def _extract_single_table(self, raw: bytes) -> bytes:
        """
        Try to keep only the first (main) table from a CSV export that may contain
        multiple tables separated by a separator pattern like:

            \r\n;\r\n
            \n;\n
            (optionally followed by extra blank lines)

        The pattern corresponds to a line containing only a single ';'
        (all-empty columns) often used as a visual spacer between exported tables.

        Returns the (possibly) truncated bytes. Falls back to original on errors.
        """
        try:
            text = raw.decode("utf-8-sig", errors="replace")
        except Exception:  # pragma: no cover - very unlikely
            logging.debug("Failed to decode raw bytes, returning original")
            return raw

        # Candidate separator patterns ordered by specificity (longest first)
        patterns = [
            "\r\n;\r\n\r\n",
            "\r\n;\r\n",
            "\n;\n\n",
            "\n;\n",
        ]

        cut_idx = None
        matched_pat = None
        for pat in patterns:
            idx = text.find(pat)
            if idx != -1:
                cut_idx = idx
                matched_pat = pat
                break

        if cut_idx is None or matched_pat is None:
            return raw  # nothing to do
        # Return the part AFTER the first separator pattern instead of before it
        start_idx = cut_idx + len(matched_pat)
        second_part = text[start_idx:].lstrip("\r\n")
        # Ensure it ends with a newline for CSV parsers
        if not second_part.endswith("\n"):
            second_part += "\n"
        truncated = second_part
        logging.debug(
            "CSV truncated at separator pattern; original=%d bytes, truncated=%d bytes",
            len(raw),
            len(truncated.encode("utf-8")),
        )
        return truncated.encode("utf-8")

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

    def _row_to_parsed(self, row: pd.Series, account_map: dict[str, Account]) -> Transaction:
        """Parse a dataframe row into a validated Transaction instance (for DAO.bulk_create).

        Injects the resolved `account_id` based on the account number.
        """
        transaction_in = TransactionIn(**row.to_dict())
        account = account_map.get(transaction_in.account)
        if account is None:
            raise ValueError(f"Account not found for number: {transaction_in.account}")
        transaction_in.account_id = account.id
        try:
            return Transaction.model_validate(transaction_in)
        except ValidationError as exc:
            print(repr(exc.errors()[0]["type"]))
            logger.error("Failed to validate transaction row: %s", exc, exc_info=True)
            raise
