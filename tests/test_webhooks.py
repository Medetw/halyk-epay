"""Tests for ``WebhookParser`` and ``WebhookVerifier``.

We cover:
- snake_case + camelCase key compatibility
- HMAC happy path (hex + base64)
- tamper detection
- malformed signature → typed error
"""

from __future__ import annotations

import base64
import hashlib
import hmac

import pytest

from halyk_epay import HalykError, HalykSignatureError, WebhookParser, WebhookVerifier


def _sign(body: bytes, secret: str, *, encoding: str = "hex") -> str:
    raw = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return raw.hex() if encoding == "hex" else base64.b64encode(raw).decode()


class TestParser:
    def test_parses_camel_case(self, hosted_page_callback_body: bytes) -> None:
        event = WebhookParser.parse(hosted_page_callback_body)
        assert event.invoice_id == "ord-001"
        assert event.is_success
        assert event.amount == 10_000
        assert event.reference == "123456789012"
        assert event.halyk_id == "halyk-uid-xyz"
        assert event.raw["invoiceId"] == "ord-001"

    def test_parses_snake_case(self) -> None:
        event = WebhookParser.parse(b'{"invoice_id":"ord-002","code":"error"}')
        assert event.invoice_id == "ord-002"
        assert not event.is_success

    def test_rejects_non_json(self) -> None:
        with pytest.raises(HalykError):
            WebhookParser.parse(b"not json at all")

    def test_rejects_array_payload(self) -> None:
        with pytest.raises(HalykError):
            WebhookParser.parse(b'["nope"]')


class TestVerifier:
    def test_hex_signature_happy_path(
        self, webhook_secret: str, hosted_page_callback_body: bytes
    ) -> None:
        v = WebhookVerifier(webhook_secret, encoding="hex")
        sig = _sign(hosted_page_callback_body, webhook_secret, encoding="hex")
        event = v.parse_and_verify(hosted_page_callback_body, signature=sig)
        assert event.invoice_id == "ord-001"

    def test_base64_signature_happy_path(
        self, webhook_secret: str, hosted_page_callback_body: bytes
    ) -> None:
        v = WebhookVerifier(webhook_secret, encoding="base64")
        sig = _sign(hosted_page_callback_body, webhook_secret, encoding="base64")
        event = v.parse_and_verify(hosted_page_callback_body, signature=sig)
        assert event.is_success

    def test_tampered_body_fails(
        self, webhook_secret: str, hosted_page_callback_body: bytes
    ) -> None:
        v = WebhookVerifier(webhook_secret)
        sig = _sign(hosted_page_callback_body, webhook_secret)
        tampered = hosted_page_callback_body.replace(b"10000", b"99999")
        with pytest.raises(HalykSignatureError):
            v.verify(tampered, sig)

    def test_malformed_signature(
        self, webhook_secret: str, hosted_page_callback_body: bytes
    ) -> None:
        v = WebhookVerifier(webhook_secret, encoding="hex")
        with pytest.raises(HalykSignatureError):
            v.verify(hosted_page_callback_body, "not-hex-zz")

    def test_empty_secret_rejected(self) -> None:
        with pytest.raises(ValueError):
            WebhookVerifier("")
