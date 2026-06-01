"""Thin httpx wrapper that handles auth, retries, and error translation.

Resources (invoices, payments) call ``HttpTransport.request_json(...)`` and
get back parsed JSON or a typed ``HalykError`` exception.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from halyk_epay.auth import TokenManager
from halyk_epay.exceptions import HalykAPIError, HalykNetworkError

_RETRY_STATUS = {502, 503, 504}
_DEFAULT_RETRIES = 2
_DEFAULT_BACKOFF = 0.5


class HttpTransport:
    def __init__(
        self,
        http: httpx.AsyncClient,
        token_manager: TokenManager,
        api_url: str,
        retries: int = _DEFAULT_RETRIES,
        backoff: float = _DEFAULT_BACKOFF,
    ) -> None:
        self._http = http
        self._tokens = token_manager
        self._api_url = api_url.rstrip("/")
        self._retries = retries
        self._backoff = backoff

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        scope: str = "payment",
        expect_status: tuple[int, ...] = (200, 201),
    ) -> dict[str, Any]:
        url = f"{self._api_url}/{path.lstrip('/')}"
        attempt = 0
        last_exc: Exception | None = None

        while attempt <= self._retries:
            token = await self._tokens.get(scope)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            try:
                resp = await self._http.request(
                    method, url, json=json_body, headers=headers
                )
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt == self._retries:
                    raise HalykNetworkError(f"{method} {url} failed: {exc}") from exc
                await asyncio.sleep(self._backoff * (2**attempt))
                attempt += 1
                continue

            if resp.status_code == 401:
                # Token expired mid-request — invalidate and retry once.
                self._tokens.invalidate(scope)
                if attempt < self._retries:
                    attempt += 1
                    continue

            if resp.status_code in _RETRY_STATUS and attempt < self._retries:
                await asyncio.sleep(self._backoff * (2**attempt))
                attempt += 1
                continue

            if resp.status_code not in expect_status:
                raise HalykAPIError(
                    status_code=resp.status_code,
                    message=_extract_error_message(resp),
                    body=resp.text,
                )

            try:
                return resp.json()  # type: ignore[no-any-return]
            except json.JSONDecodeError as exc:
                raise HalykAPIError(
                    status_code=resp.status_code,
                    message=f"non-JSON response: {resp.text[:200]}",
                    body=resp.text,
                ) from exc

        # Unreachable, but mypy needs it.
        raise HalykNetworkError(str(last_exc) if last_exc else "exhausted retries")


def _extract_error_message(resp: httpx.Response) -> str:
    try:
        body = resp.json()
    except json.JSONDecodeError:
        return resp.text[:300]
    if isinstance(body, dict):
        return str(body.get("message") or body.get("error") or body)[:300]
    return str(body)[:300]
