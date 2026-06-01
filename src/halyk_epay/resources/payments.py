"""Payment resource — cryptogram (direct API) flow.

NOTE on scope: v0.1 ships ``charge`` (one-shot) — auth/capture two-step
and refunds will land in v0.2 once we lock down the contract differences
between the legacy ``/payment`` and newer ``/payments`` endpoints.
"""

from __future__ import annotations

from halyk_epay._http import HttpTransport
from halyk_epay.models.payment import Charge


class Payments:
    def __init__(self, transport: HttpTransport, shop_id: str) -> None:
        self._t = transport
        self._shop_id = shop_id

    async def charge(
        self,
        *,
        invoice_id: str,
        amount: int,
        currency: str,
        cryptogram: str,
        description: str | None = None,
    ) -> Charge:
        """One-shot charge with an already-built cryptogram.

        Use ``halyk_epay.build_cryptogram(...)`` to produce the cryptogram
        string from raw card data on the merchant side (never send raw PAN
        to your own backend).
        """
        body: dict[str, object] = {
            "shop_id": self._shop_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "currency": currency,
            "cryptogram": cryptogram,
        }
        if description is not None:
            body["description"] = description

        data = await self._t.request_json("POST", "/payment/cryptopay", json_body=body)
        data.setdefault("invoice_id", invoice_id)
        data.setdefault("amount", amount)
        data.setdefault("currency", currency)
        return Charge.model_validate(data)
