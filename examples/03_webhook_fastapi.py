"""FastAPI webhook handler — verify Halyk ``postLink`` callbacks.

If your merchant agreement includes signed callbacks, use ``WebhookVerifier``.
Otherwise drop to ``WebhookParser.parse(...)`` and validate the result
against your own DB-stored invoice (compare amount, status, currency).

Run:
    pip install fastapi uvicorn
    export HALYK_WEBHOOK_SECRET=...
    uvicorn examples.03_webhook_fastapi:app --reload
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException, Request

from halyk_epay import HalykSignatureError, WebhookParser, WebhookVerifier

app = FastAPI()

_secret = os.getenv("HALYK_WEBHOOK_SECRET")
_verifier = WebhookVerifier(_secret) if _secret else None
_parser = WebhookParser()


@app.post("/halyk-webhook")
async def halyk_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
) -> dict[str, str]:
    body = await request.body()

    try:
        if _verifier is not None:
            if x_signature is None:
                raise HTTPException(status_code=401, detail="missing signature")
            event = _verifier.parse_and_verify(body, signature=x_signature)
        else:
            event = _parser.parse(body)
    except HalykSignatureError:
        raise HTTPException(status_code=401, detail="invalid signature") from None

    if event.is_success:
        # TODO: mark order ``event.invoice_id`` as paid in your DB.
        # TODO: notify the user.
        return {"status": "ok"}

    # TODO: mark order as failed, log ``event.raw`` for audit.
    return {"status": "noted"}
