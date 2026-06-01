"""Webhook handling — parse + (optionally) verify Halyk ``postLink`` callbacks.

Two helpers:

* ``WebhookParser`` — turn raw bytes into a typed :class:`WebhookEvent`.
  Use this if your merchant agreement does not include signed callbacks.

* ``WebhookVerifier`` — HMAC-SHA256 verification with constant-time compare.
  Wire your shared secret + signature header name in once; on every webhook
  call ``.parse_and_verify(body, signature)``.

Halyk historically delivers signature in the ``X-Signature`` (or similar)
header as hex or base64. Check your merchant cabinet for the exact name
and encoding, then pass them via the constructor.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from typing import Literal

from halyk_epay.exceptions import HalykError, HalykSignatureError
from halyk_epay.models.webhook import WebhookEvent

SignatureEncoding = Literal["hex", "base64"]


class WebhookParser:
    """Parses a Halyk ``postLink`` JSON body into :class:`WebhookEvent`."""

    @staticmethod
    def parse(body: bytes | str) -> WebhookEvent:
        if isinstance(body, bytes):
            try:
                body_str = body.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise HalykError(f"webhook body is not UTF-8: {exc}") from exc
        else:
            body_str = body

        try:
            data = json.loads(body_str)
        except json.JSONDecodeError as exc:
            raise HalykError(f"webhook body is not valid JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise HalykError(f"webhook body is not a JSON object, got {type(data).__name__}")

        return WebhookEvent.model_validate(data)


class WebhookVerifier:
    """HMAC-SHA256 signature verifier for signed callbacks.

    Usage::

        verifier = WebhookVerifier(secret=os.environ["HALYK_WEBHOOK_SECRET"])

        @app.post("/halyk-webhook")
        async def webhook(request: Request):
            body = await request.body()
            sig  = request.headers["X-Signature"]
            event = verifier.parse_and_verify(body, signature=sig)
            ...
    """

    def __init__(
        self,
        secret: str | bytes,
        *,
        encoding: SignatureEncoding = "hex",
        algorithm: str = "sha256",
    ) -> None:
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if not secret:
            raise ValueError("webhook secret must not be empty")
        if algorithm not in hashlib.algorithms_guaranteed:
            raise ValueError(f"unsupported HMAC algorithm: {algorithm}")
        self._secret = secret
        self._encoding = encoding
        self._algorithm = algorithm
        self._parser = WebhookParser()

    def verify(self, body: bytes, signature: str) -> None:
        """Raise :class:`HalykSignatureError` if the signature does not match."""
        expected = hmac.new(self._secret, body, self._algorithm).digest()
        try:
            actual = (
                bytes.fromhex(signature)
                if self._encoding == "hex"
                else base64.b64decode(signature, validate=True)
            )
        except (ValueError, binascii.Error) as exc:
            raise HalykSignatureError(
                f"signature is not valid {self._encoding}: {exc}"
            ) from exc

        if not hmac.compare_digest(expected, actual):
            raise HalykSignatureError("HMAC signature mismatch")

    def parse_and_verify(self, body: bytes, *, signature: str) -> WebhookEvent:
        self.verify(body, signature)
        return self._parser.parse(body)
