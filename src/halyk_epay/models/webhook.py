"""Webhook event model — Halyk ``postLink`` callback.

Real-world callback payloads from Halyk use ``camelCase`` keys
(``invoiceId``) but some integrations show ``snake_case`` (``invoice_id``).
The parser accepts both via field aliases.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WebhookCode(str, Enum):
    OK = "ok"
    ERROR = "error"


class WebhookEvent(BaseModel):
    """Parsed Halyk postLink callback.

    Fields kept conservative — Halyk has been known to add/remove fields
    over time. ``raw`` always contains the full original payload.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    invoice_id: str = Field(..., alias="invoiceId", description="Merchant order id.")
    code: WebhookCode = Field(..., description="'ok' or 'error'.")
    amount: float | None = None
    reference: str | None = Field(default=None, description="Bank RRN.")
    halyk_id: str | None = Field(default=None, alias="id", description="Halyk-side payment id.")
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _stash_raw(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)  # copy
            data["raw"] = dict(data)
        return data

    @property
    def is_success(self) -> bool:
        return self.code == WebhookCode.OK
