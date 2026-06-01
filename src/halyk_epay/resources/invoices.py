"""Invoice resource — hosted payment page flow."""

from __future__ import annotations

from halyk_epay._http import HttpTransport
from halyk_epay.models.invoice import Invoice, InvoiceCreate


class Invoices:
    def __init__(self, transport: HttpTransport, shop_id: str) -> None:
        self._t = transport
        self._shop_id = shop_id

    async def create(self, invoice: InvoiceCreate) -> Invoice:
        """Create a hosted-page invoice. Returns ``Invoice`` with ``invoice_url``."""
        payload = invoice.model_dump(exclude_none=True)
        payload["shop_id"] = self._shop_id
        if "failure_post_link" not in payload and "post_link" in payload:
            payload["failure_post_link"] = payload["post_link"]

        data = await self._t.request_json("POST", "/invoice", json_body=payload, scope="payment")
        # Halyk returns a flat object — merge merchant-side fields for convenience.
        data.setdefault("invoice_id", invoice.invoice_id)
        data.setdefault("amount", invoice.amount)
        data.setdefault("currency", invoice.currency)
        return Invoice.model_validate(data)

    async def get(self, halyk_invoice_id: str) -> Invoice:
        """Look up invoice status by Halyk-side UID."""
        data = await self._t.request_json(
            "GET",
            f"/invoice/{halyk_invoice_id}",
            scope="webapi",
        )
        return Invoice.model_validate(data)
