"""End-to-end test of the cryptogram builder using a locally-generated RSA key.

We don't hit Halyk's live key URL — we generate a key in-process, build a
cryptogram, decrypt with the private half, and assert the JSON shape.
"""

from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from halyk_epay import CryptogramBuilder
from halyk_epay.models.payment import CardData


@pytest.fixture(scope="module")
def rsa_keypair() -> tuple[bytes, rsa.RSAPrivateKey]:
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem, priv


def test_cryptogram_roundtrip(rsa_keypair: tuple[bytes, rsa.RSAPrivateKey]) -> None:
    pub_pem, priv = rsa_keypair
    builder = CryptogramBuilder(
        terminal_id="test-terminal",
        public_key_pem=pub_pem,
    )
    cryptogram = builder.build(
        CardData(pan="4405639704015096", exp_month="01", exp_year="2027", cvc="321")
    )

    decrypted = priv.decrypt(base64.b64decode(cryptogram), padding.PKCS1v15())
    payload = json.loads(decrypted)
    assert payload == {
        "hpan": "4405639704015096",
        "expDate": "0127",
        "cvc": "321",
        "terminalId": "test-terminal",
    }


def test_two_digit_year_is_accepted(rsa_keypair: tuple[bytes, rsa.RSAPrivateKey]) -> None:
    pub_pem, priv = rsa_keypair
    builder = CryptogramBuilder(terminal_id="t", public_key_pem=pub_pem)
    cryptogram = builder.build(
        CardData(pan="4405639704015096", exp_month="12", exp_year="30", cvc="999")
    )
    payload = json.loads(priv.decrypt(base64.b64decode(cryptogram), padding.PKCS1v15()))
    assert payload["expDate"] == "1230"
