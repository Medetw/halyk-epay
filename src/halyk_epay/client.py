"""Public ``HalykClient`` — the only class most users need.

    async with HalykClient(client_id, client_secret, shop_id, environment="test") as h:
        invoice = await h.invoices.create(InvoiceCreate(...))
        ...

Designed as an async context manager so the underlying ``httpx.AsyncClient``
is closed deterministically (no warnings about unclosed sockets in tests).
"""

from __future__ import annotations

from types import TracebackType

import httpx

from halyk_epay._endpoints import Endpoints, Environment, resolve
from halyk_epay._http import HttpTransport
from halyk_epay.auth import TokenManager
from halyk_epay.resources.invoices import Invoices
from halyk_epay.resources.payments import Payments

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class HalykClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        shop_id: str,
        *,
        environment: Environment = "test",
        endpoints: Endpoints | None = None,
        timeout: httpx.Timeout | float = DEFAULT_TIMEOUT,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._endpoints = endpoints or resolve(environment)
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)
        self._tokens = TokenManager(
            client_id=client_id,
            client_secret=client_secret,
            oauth_url=self._endpoints.oauth_url,
            http=self._http,
        )
        transport = HttpTransport(
            http=self._http,
            token_manager=self._tokens,
            api_url=self._endpoints.api_url,
        )
        self.invoices = Invoices(transport, shop_id=shop_id)
        self.payments = Payments(transport, shop_id=shop_id)

    @property
    def endpoints(self) -> Endpoints:
        return self._endpoints

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> HalykClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
