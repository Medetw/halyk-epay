"""Exception hierarchy for halyk-epay.

    HalykError                  ← catch-all
    ├── HalykAuthError          ← OAuth token failure
    ├── HalykAPIError           ← non-2xx response from Halyk
    ├── HalykNetworkError       ← timeout / connection / DNS
    └── HalykSignatureError     ← webhook signature mismatch
"""

from __future__ import annotations


class HalykError(Exception):
    """Base class for all halyk-epay errors."""


class HalykAuthError(HalykError):
    """OAuth token request failed or expired."""


class HalykAPIError(HalykError):
    """Halyk returned a non-success HTTP status."""

    def __init__(self, status_code: int, message: str, body: str | None = None) -> None:
        super().__init__(f"Halyk API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.body = body


class HalykNetworkError(HalykError):
    """Transport-level failure (timeout, DNS, connection refused, etc.)."""


class HalykSignatureError(HalykError):
    """Webhook signature verification failed."""
