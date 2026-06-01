"""halyk-epay — async Python SDK for Halyk Bank ePay (Kazakhstan).

Quick start:

    from halyk_epay import HalykClient, InvoiceCreate

    async with HalykClient(
        client_id="...",
        client_secret="...",
        shop_id="...",
        environment="test",
    ) as halyk:
        invoice = await halyk.invoices.create(
            InvoiceCreate(
                amount=10_000,
                currency="KZT",
                invoice_id="ord-123",
                description="Order #123",
                account_id="user-42",
                back_link="https://shop.kz/success",
                failure_back_link="https://shop.kz/failure",
                post_link="https://shop.kz/webhook",
            )
        )
        print(invoice.invoice_url)

See README.md for the full guide.
"""

from halyk_epay.client import HalykClient
from halyk_epay.cryptogram import CryptogramBuilder, build_cryptogram
from halyk_epay.exceptions import (
    HalykAPIError,
    HalykAuthError,
    HalykError,
    HalykNetworkError,
    HalykSignatureError,
)
from halyk_epay.models.invoice import Invoice, InvoiceCreate, InvoiceStatus
from halyk_epay.models.payment import Charge, ChargeStatus
from halyk_epay.models.webhook import WebhookEvent
from halyk_epay.webhooks import WebhookParser, WebhookVerifier

__version__ = "0.1.0"

__all__ = [
    "Charge",
    "ChargeStatus",
    "CryptogramBuilder",
    "HalykAPIError",
    "HalykAuthError",
    "HalykClient",
    "HalykError",
    "HalykNetworkError",
    "HalykSignatureError",
    "Invoice",
    "InvoiceCreate",
    "InvoiceStatus",
    "WebhookEvent",
    "WebhookParser",
    "WebhookVerifier",
    "build_cryptogram",
    "__version__",
]
