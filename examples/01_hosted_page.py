"""Hosted Payment Page flow.

User clicks "Pay" in your app → your backend calls Halyk → Halyk returns
a URL → you redirect the browser there → user enters card on Halyk's page
→ Halyk POSTs the result to your ``post_link`` (see 03_webhook_fastapi.py).

Run:
    export HALYK_CLIENT_ID=...
    export HALYK_CLIENT_SECRET=...
    export HALYK_SHOP_ID=...
    python examples/01_hosted_page.py
"""

from __future__ import annotations

import asyncio
import os
import uuid

from halyk_epay import HalykClient, InvoiceCreate


async def main() -> None:
    async with HalykClient(
        client_id=os.environ["HALYK_CLIENT_ID"],
        client_secret=os.environ["HALYK_CLIENT_SECRET"],
        shop_id=os.environ["HALYK_SHOP_ID"],
        environment="test",
    ) as halyk:
        invoice = await halyk.invoices.create(
            InvoiceCreate(
                invoice_id=f"demo-{uuid.uuid4().hex[:8]}",
                account_id="user-42",
                amount=10_000,
                currency="KZT",
                description="Demo order",
                back_link="https://example.com/return",
                failure_back_link="https://example.com/failure",
                post_link="https://example.com/halyk-webhook",
            )
        )
        print("Halyk UID:   ", invoice.id)
        print("Merchant ID: ", invoice.invoice_id)
        print("Pay here:    ", invoice.invoice_url)


if __name__ == "__main__":
    asyncio.run(main())
