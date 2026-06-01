"""RSA cryptogram builder for the direct (cryptopay) flow.

Halyk encrypts card data merchant-side with their published RSA public key
(PKCS#1 v1.5 padding) so raw PAN never touches your servers. We mirror
that exact scheme:

    {hpan, expDate(MMYY), cvc, terminalId}  → JSON
                                            → RSA-encrypt (PKCS1v15)
                                            → base64

The public key is fetched lazily and cached in-process. Pass your own bytes
to ``CryptogramBuilder(public_key_pem=...)`` to skip the fetch (recommended
for production — pin the key in your config so a compromised CDN can't swap
keys silently).
"""

from __future__ import annotations

import base64
import json
import urllib.request
from typing import Final

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from halyk_epay._endpoints import Environment, resolve
from halyk_epay.exceptions import HalykError
from halyk_epay.models.payment import CardData

_KEY_CACHE: Final[dict[str, RSAPublicKey]] = {}


def _load_public_key(pem: bytes) -> RSAPublicKey:
    key = serialization.load_pem_public_key(pem, backend=default_backend())
    if not isinstance(key, RSAPublicKey):
        raise HalykError("Halyk public key is not RSA")
    return key


def _fetch_public_key(url: str) -> RSAPublicKey:
    if url in _KEY_CACHE:
        return _KEY_CACHE[url]
    try:
        with urllib.request.urlopen(url, timeout=10) as r:  # noqa: S310 — trusted Halyk URL
            pem = r.read()
    except Exception as exc:  # noqa: BLE001 — surface as HalykError
        raise HalykError(f"failed to fetch Halyk public key from {url}: {exc}") from exc
    key = _load_public_key(pem)
    _KEY_CACHE[url] = key
    return key


class CryptogramBuilder:
    """Reusable builder bound to a terminal_id and a public key source."""

    def __init__(
        self,
        terminal_id: str,
        *,
        environment: Environment = "test",
        public_key_pem: bytes | None = None,
        public_key_url: str | None = None,
    ) -> None:
        self._terminal_id = terminal_id
        if public_key_pem is not None:
            self._key: RSAPublicKey = _load_public_key(public_key_pem)
        else:
            url = public_key_url or resolve(environment).public_key_url
            self._key = _fetch_public_key(url)

    def build(self, card: CardData) -> str:
        exp_year = card.exp_year[-2:]  # accept YY or YYYY
        payload = {
            "hpan": card.pan.strip(),
            "expDate": f"{card.exp_month}{exp_year}",
            "cvc": card.cvc.strip(),
            "terminalId": self._terminal_id,
        }
        plain = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        encrypted = self._key.encrypt(plain, padding.PKCS1v15())
        return base64.b64encode(encrypted).decode("ascii")


def build_cryptogram(
    card: CardData,
    terminal_id: str,
    *,
    environment: Environment = "test",
    public_key_pem: bytes | None = None,
) -> str:
    """Convenience one-shot wrapper around :class:`CryptogramBuilder`."""
    return CryptogramBuilder(
        terminal_id=terminal_id,
        environment=environment,
        public_key_pem=public_key_pem,
    ).build(card)
