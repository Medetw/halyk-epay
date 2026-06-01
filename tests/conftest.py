import pytest


@pytest.fixture
def webhook_secret() -> str:
    return "test-secret-do-not-use-in-prod"


@pytest.fixture
def hosted_page_callback_body() -> bytes:
    # Shape mirrors a real Halyk postLink payload (camelCase keys).
    return (
        b'{"invoiceId":"ord-001","code":"ok","amount":10000,'
        b'"reference":"123456789012","id":"halyk-uid-xyz"}'
    )
