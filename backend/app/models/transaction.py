"""
SQLModel definitions for transactions.

Each transaction corresponds to a row in the uploaded CSV/Excel file. The model
includes optional fields for data that may not always be present. The primary
key `id` is a UUID. The `transaction_number` field is indexed
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import AliasChoices, field_validator
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Date, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .account import Account
    from .category import Category


class TransactionBase(SQLModel):
    """Shared attributes for transactions that can be inherited by other models."""

    # Raw account number to which this transaction belongs ("Rekening").
    account: str = Field(schema_extra={"validation_alias": AliasChoices("Rekening", "account")})
    # Original booking date ("Boekingsdatum"). Could be converted to date.
    booking_date: date | None = Field(
        default=None,
        sa_type=Date,
        schema_extra={"validation_alias": AliasChoices("Boekingsdatum", "booking_date")},
    )
    # Statement number ("Rekeninguittrekselnummer").
    statement_number: int | None = Field(
        default=None,
        schema_extra={
            "validation_alias": AliasChoices("Rekeninguittrekselnummer", "statement_number")
        },
    )
    # Unique transaction number ("Transactienummer").
    # Database constraint (unique=True) will enforce uniqueness among non-null values (PostgreSQL allows multiple NULLs).
    transaction_number: int | None = Field(
        default=None,
        index=True,
        schema_extra={"validation_alias": AliasChoices("Transactienummer", "transaction_number")},
    )
    # Counterparty account ("Rekening tegenpartij").
    counterparty_account: str | None = Field(
        default=None,
        schema_extra={
            "validation_alias": AliasChoices("Rekening tegenpartij", "counterparty_account")
        },
    )
    # Counterparty name ("Naam tegenpartij bevat").
    counterparty_name: str | None = Field(
        default=None,
        schema_extra={
            "validation_alias": AliasChoices("Naam tegenpartij bevat", "counterparty_name")
        },
    )
    # Counterparty street and number ("Straat en nummer").
    street_number: str | None = Field(
        default=None,
        schema_extra={"validation_alias": AliasChoices("Straat en nummer", "street_number")},
    )
    # Counterparty postal code and city ("Postcode en plaats").
    postal_code_city: str | None = Field(
        default=None,
        schema_extra={"validation_alias": AliasChoices("Postcode en plaats", "postal_code_city")},
    )
    # Transaction description ("Transactie").
    transaction_type: str | None = Field(
        default=None,
        schema_extra={"validation_alias": AliasChoices("Transactie", "transaction_type")},
    )
    # Value date ("Valutadatum"). Could be converted to date.
    value_date: date | None = Field(
        default=None,
        schema_extra={"validation_alias": AliasChoices("Valutadatum", "value_date")},
    )
    # Amount ("Bedrag"). Negative values represent expenses.
    amount: Decimal = Field(schema_extra={"validation_alias": AliasChoices("Bedrag", "amount")})
    # Currency code ("Devies").
    currency: str | None = Field(
        default=None, schema_extra={"validation_alias": AliasChoices("Devies", "currency")}
    )
    # BIC code of the counterparty ("BIC").
    bic: str | None = Field(
        default=None, schema_extra={"validation_alias": AliasChoices("BIC", "bic")}
    )
    # ISO country code ("Landcode").
    country_code: str | None = Field(
        default=None, schema_extra={"validation_alias": AliasChoices("Landcode", "country_code")}
    )
    # Freeform notes ("Mededelingen").
    notes: str | None = Field(
        default=None, schema_extra={"validation_alias": AliasChoices("Mededelingen", "notes")}
    )
    # Foreign key referencing a category. Nullable until classification.
    category_id: UUID | None = Field(default=None, foreign_key="category.id")
    # Foreign key referencing the logical account entity. Nullable because
    # transactions can be ingested before accounts are defined.
    account_id: UUID | None = Field(default=None, foreign_key="account.id")


class Transaction(TransactionBase, table=True):
    """Database model for a transaction including an UUID primary key."""

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Enforce uniqueness of (account_id, transaction_number) pairs. Multiple NULLs allowed per column.
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "booking_date",
            "transaction_number",
            "counterparty_name",
            "transaction_type",
            "amount",
            "notes",
            name="uq_transaction_account_txnum",
            postgresql_nulls_not_distinct=True,
        ),
    )
    # Relationship to Category. The annotation string prevents circular import issues.
    category: Mapped[Category | None] = Relationship(
        sa_relationship=relationship(back_populates="transactions")
    )
    # Relationship to Account. Allows navigating from a transaction to its account. The attribute
    # name `account_ref" is used instead of `account` to avoid clashing with the `account`
    # column defined in `TransactionBase`.
    account_ref: Mapped[Account | None] = Relationship(
        sa_relationship=relationship(back_populates="transactions")
    )


class TransactionIn(TransactionBase):
    """Input model for creating transactions, with data validation."""

    @field_validator("amount", mode="before")
    @classmethod
    def comma_to_dot(cls, value: str) -> Decimal | None:
        if value in (None, ""):
            return None
        s = str(value).replace(",", ".")
        d = Decimal(s)
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @field_validator("booking_date", "value_date", mode="before")
    @classmethod
    def parse_date(cls, v):  # noqa: ANN001
        """Accept multiple date string formats (e.g. '02/07/2025', '2025-07-02').

        If parsing fails we return the original value so Pydantic can raise its
        standard validation error, preserving transparency.
        """
        if v in (None, ""):
            return None
        if isinstance(v, date):  # already parsed
            return v
        if not isinstance(v, str):
            return v
        raw = v.strip()
        # Normalize common separators
        normalized = raw.replace(".", "/").replace("-", "/")
        patterns = [
            "%d/%m/%Y",  # European style (most likely for provided data)
            "%Y/%m/%d",  # ISO with slashes
            "%Y/%d/%m",  # fallback just in case
        ]
        for fmt in patterns:
            try:
                return datetime.strptime(normalized, fmt).date()
            except ValueError:
                continue
        # Last attempt: ISO directly (YYYY-MM-DD) if user already in that style
        try:
            return datetime.fromisoformat(raw).date()
        except Exception:  # pragma: no cover - fall through to pydantic error
            return v


class TransactionOut(TransactionBase):
    id: UUID
    # Expose category name directly for frontend convenience
    category: str | None = None
