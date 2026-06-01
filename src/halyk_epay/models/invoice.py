"""Invoice models — hosted payment page flow."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Currency = Literal["KZT", "USD", "EUR", "RUB"]
Language = Literal["rus", "kaz", "eng"]


class InvoiceStatus(str, Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"


class InvoiceCreate(BaseModel):
    """Request body for ``POST /invoice``.

    Field names mirror the Halyk request schema as observed in production
    integrations. ``account_id`` is the merchant's user identifier;
    ``invoice_id`` is the merchant-side order id (unique per shop).
    """

    model_config = ConfigDict(extra="allow")

    invoice_id: str = Field(..., description="Merchant order id, unique per shop.")
    account_id: str = Field(..., description="Merchant-side payer/user identifier.")
    amount: int = Field(..., gt=0, description="Amount in minor units (e.g. tenge).")
    currency: Currency = "KZT"
    description: str = Field(..., max_length=125)
    language: Language = "rus"
    expire_period: str = Field(default="1d", description="Halyk format, e.g. '1d', '30m'.")

    # Redirect URLs shown to the user.
    back_link: str = Field(..., description="Browser redirect on success.")
    failure_back_link: str = Field(..., description="Browser redirect on failure.")

    # Server-to-server webhook URLs.
    post_link: str = Field(..., description="Server callback on success.")
    failure_post_link: str | None = Field(
        default=None, description="Server callback on failure (defaults to post_link)."
    )

    # Optional notification channels.
    recipient_contact: str | None = Field(default=None, description="Email for receipt.")
    recipient_contact_sms: str | None = Field(default=None, description="Phone for SMS receipt.")
    notifier_contact_sms: str | None = Field(default=None)


class Invoice(BaseModel):
    """Response from invoice creation or lookup."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Halyk-side invoice UID.")
    invoice_id: str = Field(..., description="Merchant order id echoed back.")
    invoice_url: str | None = Field(default=None, description="Hosted page URL.")
    amount: int
    currency: Currency
    status: InvoiceStatus = InvoiceStatus.NEW
