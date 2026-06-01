"""OAuth ``client_credentials`` flow with in-memory token caching.

Halyk issues short-lived access tokens (typically 5-15 min). We cache the
token until ``expires_at - leeway`` and refresh on demand.

Scope semantics from Halyk docs:
- ``payment``  — create invoices, charges
- ``webapi``   — read invoices, refund/cancel
- ``usercred`` — manage saved cards (out of scope for v0.1)
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from halyk_epay.exceptions import HalykAuthError, HalykNetworkError

DEFAULT_LEEWAY_SECONDS = 30


@dataclass
class _CachedToken:
    access_token: str
    expires_at: float  # unix seconds


class TokenManager:
    """Caches OAuth tokens per scope.

    Thread-/task-safety: a single ``TokenManager`` instance is intended to be
    used from a single asyncio event loop. For multi-process usage create one
    instance per process.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        oauth_url: str,
        http: httpx.AsyncClient,
        leeway_seconds: int = DEFAULT_LEEWAY_SECONDS,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._oauth_url = oauth_url.rstrip("/")
        self._http = http
        self._leeway = leeway_seconds
        self._cache: dict[str, _CachedToken] = {}

    async def get(self, scope: str = "payment") -> str:
        cached = self._cache.get(scope)
        if cached and cached.expires_at - self._leeway > time.time():
            return cached.access_token
        return await self._fetch(scope)

    async def _fetch(self, scope: str) -> str:
        body = {
            "grant_type": "client_credentials",
            "scope": scope,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        try:
            resp = await self._http.post(
                f"{self._oauth_url}/oauth2/token",
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            raise HalykNetworkError(f"OAuth request failed: {exc}") from exc

        if resp.status_code != 200:
            raise HalykAuthError(
                f"OAuth token request failed: HTTP {resp.status_code} {resp.text[:200]}"
            )

        data = resp.json()
        token = data.get("access_token")
        expires_in = int(data.get("expires_in", 0))
        if not isinstance(token, str) or not token or expires_in <= 0:
            raise HalykAuthError(f"Malformed OAuth response: {data!r}")

        self._cache[scope] = _CachedToken(
            access_token=token,
            expires_at=time.time() + expires_in,
        )
        return token

    def invalidate(self, scope: str | None = None) -> None:
        if scope is None:
            self._cache.clear()
        else:
            self._cache.pop(scope, None)
