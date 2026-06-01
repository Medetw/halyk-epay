"""Halyk environment URLs.

Production and test endpoints are taken from Halyk ePay documentation
(see https://epayment.kz/ for the latest). If Halyk publishes new URLs,
override via ``HalykClient(..., base_urls=Endpoints(...))``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Environment = Literal["prod", "test"]


@dataclass(frozen=True)
class Endpoints:
    oauth_url: str
    api_url: str
    public_key_url: str


PROD = Endpoints(
    oauth_url="https://epay-oauth.homebank.kz",
    api_url="https://epay-api.homebank.kz",
    public_key_url="https://epay-api.homebank.kz/public.rsa",
)

TEST = Endpoints(
    oauth_url="https://test-epay-oauth.epayment.kz",
    api_url="https://test-epay-api.epayment.kz",
    public_key_url="https://test-epay-api.epayment.kz/public.rsa",
)


def resolve(env: Environment) -> Endpoints:
    return PROD if env == "prod" else TEST
