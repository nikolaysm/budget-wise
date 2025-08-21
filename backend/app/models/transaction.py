"""
SQLModel definitions for transactions.

Each transaction corresponds to a row in the uploaded CSV/Excel file. The model
includes optional fields for data that may not always be present. The primary
key `id` is an auto‑incrementing integer.
"""

from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class TransactionBase(SQLModel):
    """Shared attributes for transactions that can be inherited by other models."""

    # Raw account number to which this transaction belongs ("Rekening").
    account: str
    # Original booking date ("Boekingsdatum"). Could be converted to date.
    booking_date: Optional[str] = None
    # Statement number ("Rekeninguittrekselnummer").
    statement_number: Optional[str] = None
    # Unique transaction number ("Transactienummer").
    transaction_number: Optional[str] = None
    # Counterparty account ("Rekening tegenpartij").
    counterparty_account: Optional[str] = None
    # Counterparty name ("Naam tegenpartij bevat").
    counterparty_name: Optional[str] = None
    # Counterparty street and number ("Straat en nummer").
    street_number: Optional[str] = None
    # Counterparty postal code and city ("Postcode en plaats").
    postal_code_city: Optional[str] = None
    # Transaction description ("Transactie").
    transaction_type: Optional[str] = None
    # Value date ("Valutadatum"). Could be converted to date.
    value_date: Optional[str] = None
    # Amount ("Bedrag"). Negative values represent expenses.
    amount: float
    # Currency code ("Devies").
    currency: Optional[str] = None
    # BIC code of the counterparty ("BIC").
    bic: Optional[str] = None
    # ISO country code ("Landcode").
    country_code: Optional[str] = None
    # Freeform notes ("Mededelingen").
    notes: Optional[str] = None
    # Foreign key referencing a category. Nullable until classification.
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    # Foreign key referencing the logical account entity. Nullable because
    # transactions can be ingested before accounts are defined.
    account_id: Optional[int] = Field(default=None, foreign_key="account.id")


class Transaction(TransactionBase, table=True):
    """Database model for a transaction including an auto‑incrementing primary key."""

    id: Optional[int] = Field(default=None, primary_key=True)
    # Relationship to Category. The annotation string prevents circular import issues.
    category: Optional["Category"] = Relationship(back_populates="transactions")
    # Relationship to Account. Allows navigating from a transaction to its account. The attribute
    # name `account_ref` is used instead of `account` to avoid clashing with the `account`
    # column defined in `TransactionBase`.
    account_ref: Optional["Account"] = Relationship(back_populates="transactions")