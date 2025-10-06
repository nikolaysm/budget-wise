"""Business logic for transactions (parsing & ingestion)."""

from __future__ import annotations

import io
import logging
import re
from datetime import date
from decimal import Decimal
from functools import cached_property

import numpy as np
import pandas as pd
from pydantic import ValidationError

from app.core.config import get_settings
from app.daos.account_dao import AccountDAO
from app.daos.category_dao import CategoryDAO
from app.daos.transaction_dao import TransactionDAO
from app.models.account import Account
from app.models.transaction import Transaction, TransactionIn
from app.schemas import (
    CategorySummaryItem,
    CategorySummaryOut,
    PaginationIn,
    SortParams,
    TransactionFilters,
)
from app.services.ai_service import AIInferenceService

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

    to_strip: list[str] = ["smirnov", "olga", "nikolay", "viktoria", "alexander"]
    _NAME_STRIP_RE: re.Pattern[str] | None = None  # lazy-compiled regex for name removal

    @classmethod
    def _get_name_strip_re(cls) -> re.Pattern[str]:
        if cls._NAME_STRIP_RE is None:
            cls._NAME_STRIP_RE = re.compile(
                r"\b(" + "|".join(re.escape(n) for n in cls.to_strip) + r")\b", re.IGNORECASE
            )
        return cls._NAME_STRIP_RE

    def __init__(
        self,
        dao: TransactionDAO,
        account_dao: AccountDAO,
        category_dao: CategoryDAO,
        classifier: AIInferenceService | None = None,
    ):
        self.dao = dao
        self.account_dao = account_dao
        self.category_dao = category_dao
        self.classifier = classifier or AIInferenceService()

    # --- Cached data --------------------------------------------------------
    @cached_property
    def _category_labels(self) -> list[str]:  # pragma: no cover - trivial accessor
        """Cached flattened label surface used for ML classification.

        Combines category.name, expanded_phrase (if present), and aliases while
        preserving order of categories and stable uniqueness. This ensures the
        ML model sees the broader semantic surface without exploding duplicates.

        NOTE: Process-lifetime cache; call `refresh_category_cache()` after any
        create/update/delete that changes names/phrases/aliases.
        """
        labels: list[str] = []
        seen: set[str] = set()
        for c in self._list_categories_for_cache():
            for candidate in [c.name, getattr(c, "expanded_phrase", None)]:
                if candidate and candidate not in seen:
                    seen.add(candidate)
                    labels.append(candidate)
            # aliases is list[str]
            for a in getattr(c, "aliases", []) or []:
                if a and a not in seen:
                    seen.add(a)
                    labels.append(a)
        return labels

    def refresh_category_cache(self) -> None:
        """Invalidate cached category labels so next access re-queries DB."""
        self.__dict__.pop("_category_labels", None)

    # --- Public API -----------------------------------------------------------
    def list(
        self,
        *,
        pagination: PaginationIn,
        sorting: SortParams,
        filters: TransactionFilters | None = None,
    ) -> list[Transaction]:
        return self.dao.list(pagination=pagination, sorting=sorting, filters=filters)

    def list_and_count(
        self,
        *,
        pagination: PaginationIn,
        sorting: SortParams,
        filters: TransactionFilters | None = None,
    ) -> tuple[list[Transaction], int]:
        return self.dao.list_and_count(pagination=pagination, sorting=sorting, filters=filters)

    def get(self, tx_id) -> Transaction | None:  # accepts UUID string
        return self.dao.get(tx_id)

    def categorization_stats(self) -> dict[str, int]:
        """Expose categorization statistics via service layer (delegates to DAO)."""
        return self.dao.count_categorization_stats()

    def category_summary(
        self, *, date_from: date | str | None = None, date_to: date | str | None = None
    ) -> CategorySummaryOut:
        """Return aggregated totals grouped by category within optional date range.

        Accepts either date objects (preferred) or YYYY-MM-DD strings (backward compatibility).
        """
        df: date | None
        dt: date | None
        if isinstance(date_from, str) and date_from:
            try:
                df = date.fromisoformat(date_from)
            except ValueError:  # pragma: no cover - invalid input fallback
                df = None
        else:
            df = date_from if isinstance(date_from, date) else None
        if isinstance(date_to, str) and date_to:
            try:
                dt = date.fromisoformat(date_to)
            except ValueError:  # pragma: no cover
                dt = None
        else:
            dt = date_to if isinstance(date_to, date) else None

        raw = self.dao.category_summary(date_from=df, date_to=dt)
        items: list[CategorySummaryItem] = []
        for r in raw:
            cat_raw = r.get("category")
            category = str(cat_raw) if cat_raw not in (None, "") else None
            count_raw = r.get("count", 0)
            try:
                count_val = int(count_raw)  # type: ignore[arg-type]
            except Exception:  # pragma: no cover - fallback
                count_val = 0
            amt_raw = r.get("total_amount", 0)
            try:
                if isinstance(amt_raw, Decimal):
                    total_amt = amt_raw
                else:
                    total_amt = Decimal(str(amt_raw))
            except Exception:  # pragma: no cover - fallback
                total_amt = Decimal(0)
            items.append(
                CategorySummaryItem(
                    category=category,
                    count=count_val,
                    total_amount=total_amt,
                )
            )
        total_amount: Decimal = sum((i.total_amount for i in items), Decimal(0))
        total_count = sum(i.count for i in items)
        return CategorySummaryOut(
            items=items,
            date_from=df.isoformat() if df else None,
            date_to=dt.isoformat() if dt else None,
            total_amount=total_amount,
            total_count=total_count,
        )

    def ingest_file(self, *, filename: str, data: bytes) -> list[Transaction]:
        """Parse the uploaded file and persist each transaction."""
        table_data = self._extract_single_table(data)
        df = self._read_file(filename=filename, data=table_data).replace({np.nan: None})
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

    def set_transaction_number(self, tx_id: str, number: int) -> Transaction:
        """Assign a transaction_number to an existing transaction.

        Raises ValueError if transaction not found.
        """
        updated = self.dao.set_transaction_number(tx_id, number)
        if not updated:
            raise ValueError("Transaction not found")
        # Re-fetch to return with relationships if needed
        tx = self.get(tx_id)
        if tx is None:  # pragma: no cover - defensive, should not happen
            raise ValueError("Transaction not found after update")
        return tx

    # --- Category suggestion -----------------------------------------------
    def suggest_category_for(
        self,
        tx_id: str,
        *,
        threshold: float = 0.5,
        auto_assign: bool = True,
        commit: bool = True,
    ) -> tuple[str | None, float | None, str, str | None]:
        """Suggest a category name for a transaction.

        Returns (category_name|None, score|None, reason, counterparty_name|None)
        Reason gives a short explanation (e.g. 'ml', 'rule:name match', 'no-text').
        """
        tx = self.get(tx_id)
        if tx is None:
            raise ValueError("Transaction not found")
        # Aggregate text fields.
        # Strategy:
        #   - Keep counterparty_name, but remove a small set of personal names (self.to_strip)
        #   - Strip digits only from the other more free-form fields (transaction_type, notes)
        #   - Collapse whitespace after cleaning
        name_part = tx.counterparty_name or ""
        other_raw = " \n".join(p for p in [tx.transaction_type, tx.notes] if p)
        # Strip digits from the non-name portion only
        other_no_digits = re.sub(r"\d+", " ", other_raw)
        other_norm = " ".join(other_no_digits.split())
        all_parts = f"{name_part} {other_norm}"
        # Remove personal names (one-time compiled regex) to reduce bias
        all_striped = self._get_name_strip_re().sub(" ", all_parts)
        text = " ".join(all_striped.split())
        if not text.strip():
            return None, None, "no-text", tx.counterparty_name
        # Fetch (cached) category labels (flattened surface)
        surface_labels = self._category_labels
        if not surface_labels:
            return None, None, "no-categories", tx.counterparty_name

        # Prepare mapping from variant -> canonical (first variant maps to its base name)
        variant_to_canonical: dict[str, str] = {}
        for c in self._list_categories_for_cache():
            base = c.name
            variants = [c.name]
            if getattr(c, "expanded_phrase", None):  # keep guard for missing attr in older objects
                variants.append(c.expanded_phrase)  # type: ignore[attr-defined]
            for a in getattr(c, "aliases", []) or []:  # type: ignore[attr-defined]
                variants.append(a)
            for v in variants:
                if v not in variant_to_canonical:
                    variant_to_canonical[v] = base

        # ML prediction (hybrid embedding + optional LLM)
        pred, reason_code = self.classifier.suggest_best_hybrid(
            text=text, candidate_labels=surface_labels, mode="auto"
        )
        if not pred:
            return None, None, "no-prediction", tx.counterparty_name
        canonical = variant_to_canonical.get(pred.label, pred.label)
        reason_final = reason_code if canonical == pred.label else f"{reason_code}:variant"
        # Delegate any optional auto-assignment (side-effect) to helper for separation of concerns
        self._maybe_assign_category(
            tx,
            canonical,
            pred.score,
            reason_final,
            threshold=threshold,
            auto_assign=auto_assign,
            commit=commit,
        )
        return canonical, pred.score, reason_final, tx.counterparty_name

    def bulk_suggest_categories(self, *, limit: int = 50, threshold: float = 0.5) -> list[dict]:
        """Suggest (and auto-assign) categories for uncategorized transactions.

        Behaviour:
          * Gathers up to `limit` most recent uncategorized transactions.
          * Runs ML hybrid suggestion only (no legacy substring heuristic).
          * If a suggestion exists and score >= threshold it will assign the category immediately
            (if the category name exists).
          * Returns a list of dictionaries containing: id, suggested, score, reason, assigned(bool), counterparty_name.
        """
        pagination = PaginationIn(offset=0, limit=limit)
        sorting = SortParams(sort_by="booking_date", sort_dir="desc")
        filters = TransactionFilters(has_category=False)
        rows = self.dao.list(pagination=pagination, sorting=sorting, filters=filters)

        out: list[dict] = []
        any_assigned = False
        for tx in rows:
            try:
                # Defer commit for batch efficiency
                suggested, score, reason, counterparty_name = self.suggest_category_for(
                    str(tx.id), threshold=threshold, auto_assign=True, commit=False
                )
            except ValueError:
                logger.error("Failed to suggest category for transaction id=%s", str(tx.id))
                continue
            assigned = tx.category_id is not None
            if assigned:
                any_assigned = True
            out.append(
                {
                    "id": str(tx.id),
                    "suggested": suggested,
                    "score": score,
                    "reason": reason,
                    "assigned": assigned,
                    "counterparty_name": counterparty_name,
                }
            )
        if any_assigned:
            # Commit via DAO abstraction (DAO owns the session lifecycle interaction)
            try:
                self.dao.commit()
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed committing assigned categories; rolling back via DAO")
                try:
                    self.dao.rollback()
                except Exception:  # pragma: no cover - nested failure
                    logger.exception("Rollback via DAO also failed")
        return out

    # Helper to list categories for caching / label building
    def _list_categories_for_cache(self):  # -> list[Category]: circular import avoidance in typing
        pag = PaginationIn(offset=0, limit=500)
        sort = SortParams(sort_by=None, sort_dir=None)
        return self.category_dao.list(pagination=pag, sorting=sort, filters=None)

    # --- Internal helpers -----------------------------------------------------
    def _maybe_assign_category(
        self,
        tx: Transaction,
        category_name: str | None,
        score: float | None,
        reason: str,
        *,
        threshold: float,
        auto_assign: bool,
        commit: bool,
    ) -> bool:
        """Conditionally assign a category to a transaction.

                Returns True if an assignment occurred.

                Assignment criteria (when auto_assign is True):
                    * score >= threshold
                    * category_name resolves to an existing Category
                    * transaction not already assigned to that category

        Any database errors during commit are logged and rolled back; the
        method then returns False without raising so suggestion results aren't blocked.
        """
        if not (auto_assign and category_name):
            return False
        if not (score is not None and score >= threshold):
            return False
        cat_obj = self.category_dao.get_by_name(category_name)
        if not cat_obj:
            return False
        try:
            # Use DAO to respect data access layer abstraction
            assigned = self.dao.assign_category(tx.id, cat_obj.id, commit=commit)
            return assigned
        except Exception:  # pragma: no cover - defensive
            logger.exception("Auto-assign category via DAO failed; rolling back")
            if commit:
                try:
                    self.dao.rollback()
                except Exception:  # pragma: no cover
                    logger.exception("DAO rollback failed")
            return False

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
        # Use model_validate to avoid potential self-referential init issues in TransactionIn
        data = row.to_dict()
        transaction_in = TransactionIn.model_validate(data)
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
