"""Payment / charge models — cryptogram (direct API) flow."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ChargeStatus(str, Enum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"
    REVERSED = "REVERSED"
    FAILED = "FAILED"


class CardData(BaseModel):
    """Raw card data — passed to ``cryptogram.build()`` only.

    Never log, store, or transmit this object as-is. The SDK encrypts it
    locally with Halyk's RSA public key before any network call.
    """

    pan: str = Field(..., pattern=r"^\d{13,19}$", description="Primary account number.")
    exp_month: str = Field(..., pattern=r"^(0[1-9]|1[0-2])$", description="MM (01-12).")
    exp_year: str = Field(..., pattern=r"^\d{2,4}$", description="YY or YYYY.")
    cvc: str = Field(..., pattern=r"^\d{3,4}$", description="CVC/CVV.")


class Charge(BaseModel):
    """Response from cryptogram charge."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Halyk-side payment UID.")
    invoice_id: str
    amount: int
    currency: str
    status: ChargeStatus
    reference: str | None = Field(default=None, description="Bank RRN.")
