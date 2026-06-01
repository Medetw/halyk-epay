"""Cryptogram (direct API) flow — for in-app card forms.

The card form on YOUR frontend collects PAN/expiry/CVC, builds the
cryptogram client-side (using Halyk's public key), and sends only the
encrypted blob to your backend. Backend then calls Halyk's cryptopay
endpoint.

This example does both steps on the backend for demonstration only.
DO NOT do this in production unless your backend is PCI-compliant.

Test card (Halyk sandbox): 4405639704015096, 01/27, CVC 321.

Run:
    export HALYK_CLIENT_ID=...
    export HALYK_CLIENT_SECRET=...
    export HALYK_SHOP_ID=...
    export HALYK_TERMINAL_ID=67e34d63-102f-4bd1-898e-370781d0074d
    python examples/02_cryptogram_charge.py
"""

from __future__ import annotations

import asyncio
import os
import uuid

from halyk_epay import CryptogramBuilder, HalykClient, InvoiceCreate
from halyk_epay.models.payment import CardData


async def main() -> None:
    builder = CryptogramBuilder(
        terminal_id=os.environ["HALYK_TERMINAL_ID"],
        environment="test",
    )
    cryptogram = builder.build(
        CardData(pan="4405639704015096", exp_month="01", exp_year="27", cvc="321")
    )

    async with HalykClient(
        client_id=os.environ["HALYK_CLIENT_ID"],
        client_secret=os.environ["HALYK_CLIENT_SECRET"],
        shop_id=os.environ["HALYK_SHOP_ID"],
        environment="test",
    ) as halyk:
        merchant_invoice_id = f"demo-{uuid.uuid4().hex[:8]}"
        invoice = await halyk.invoices.create(
            InvoiceCreate(
                invoice_id=merchant_invoice_id,
                account_id="user-42",
                amount=10_000,
                currency="KZT",
                description="Cryptogram demo",
                back_link="https://example.com/return",
                failure_back_link="https://example.com/failure",
                post_link="https://example.com/halyk-webhook",
            )
        )

        charge = await halyk.payments.charge(
            invoice_id=invoice.invoice_id,
            amount=invoice.amount,
            currency=invoice.currency,
            cryptogram=cryptogram,
        )
        print("Charge status:", charge.status)
        print("RRN:          ", charge.reference)


if __name__ == "__main__":
    asyncio.run(main())
