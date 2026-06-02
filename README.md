# halyk-epay

Async Python SDK for **Halyk Bank ePay** (Kazakhstan) — hosted page, cryptogram, webhooks. Type-annotated, Pydantic-v2 models, zero magic.

[![CI](https://github.com/Medeeet/halyk-epay/actions/workflows/ci.yml/badge.svg)](https://github.com/Medeeet/halyk-epay/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/halyk-epay.svg)](https://pypi.org/project/halyk-epay/)
[![Python](https://img.shields.io/pypi/pyversions/halyk-epay.svg)](https://pypi.org/project/halyk-epay/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Why

Every Kazakhstani marketplace, e-commerce shop, and fintech app eventually integrates Halyk ePay — and ends up with the same ad-hoc `httpx.post(...)` blobs scattered across the codebase. This library extracts the well-trodden pattern into a small, well-tested package.

- **One client, three flows:** hosted page, cryptogram (direct), webhooks.
- **Async by default.** Drop into FastAPI / Starlette / aiohttp without a thread pool.
- **Typed everything.** Pydantic v2 models for requests and responses; `mypy --strict` in CI.
- **Production-grade auth.** OAuth tokens cached with leeway, auto-refreshed on 401, retried on 5xx with exponential backoff.
- **Honest webhook security.** Optional HMAC-SHA256 verification with constant-time compare; documented for the *prevalent-but-undocumented* case where merchants don't have signed callbacks.

## Install

```bash
pip install halyk-epay
```

Requires Python 3.10+.

## Quick start

### Hosted payment page (most common)

```python
import asyncio
from halyk_epay import HalykClient, InvoiceCreate


async def main():
    async with HalykClient(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        shop_id="YOUR_SHOP_ID",
        environment="test",  # or "prod"
    ) as halyk:
        invoice = await halyk.invoices.create(
            InvoiceCreate(
                invoice_id="ord-001",
                account_id="user-42",
                amount=10_000,             # KZT, in tenge
                currency="KZT",
                description="Order #001",
                back_link="https://shop.kz/return",
                failure_back_link="https://shop.kz/failure",
                post_link="https://shop.kz/halyk-webhook",
            )
        )
        print(invoice.invoice_url)  # redirect the user here


asyncio.run(main())
```

### Cryptogram (direct API)

For in-app card forms where you collect card data yourself.
**Note:** your environment must be PCI-DSS compliant to handle raw PAN.

```python
from halyk_epay import CryptogramBuilder, HalykClient
from halyk_epay.models.payment import CardData

builder = CryptogramBuilder(terminal_id="...", environment="test")
cryptogram = builder.build(
    CardData(pan="4405639704015096", exp_month="01", exp_year="27", cvc="321")
)

async with HalykClient(...) as halyk:
    charge = await halyk.payments.charge(
        invoice_id="ord-001",
        amount=10_000,
        currency="KZT",
        cryptogram=cryptogram,
    )
    print(charge.status)
```

### Webhook (FastAPI)

```python
from fastapi import FastAPI, Header, HTTPException, Request
from halyk_epay import HalykSignatureError, WebhookVerifier

app = FastAPI()
verifier = WebhookVerifier(secret="...")

@app.post("/halyk-webhook")
async def webhook(request: Request, x_signature: str = Header(alias="X-Signature")):
    body = await request.body()
    try:
        event = verifier.parse_and_verify(body, signature=x_signature)
    except HalykSignatureError:
        raise HTTPException(status_code=401)
    if event.is_success:
        # mark order event.invoice_id as paid
        ...
    return {"status": "ok"}
```

If your merchant agreement doesn't include signed callbacks, use `WebhookParser.parse(body)` directly and validate against your stored invoice (amount, currency, status).

See the [`examples/`](./examples) directory for runnable scripts.

## Test sandbox

Halyk publishes a sandbox at `testepay.homebank.kz` with these credentials:

- **Test card:** `4405639704015096`, expiry `01/27`, CVC `321`
- **Test terminal id:** `67e34d63-102f-4bd1-898e-370781d0074d`
- **Public RSA key:** [`https://test-epay-api.epayment.kz/public.rsa`](https://test-epay-api.epayment.kz/public.rsa)

Pass `environment="test"` to `HalykClient` and `CryptogramBuilder` and you're on the sandbox.

## API surface

| Resource | Method | Notes |
|---|---|---|
| `client.invoices.create(InvoiceCreate)` | `POST /invoice` | Hosted page flow. |
| `client.invoices.get(halyk_uid)` | `GET /invoice/{id}` | Status lookup. |
| `client.payments.charge(...)` | `POST /payment/cryptopay` | One-shot cryptogram charge. |
| `CryptogramBuilder(terminal_id, ...).build(CardData)` | local | RSA-PKCS1v15, base64. |
| `WebhookParser.parse(body)` | local | snake_case + camelCase. |
| `WebhookVerifier(secret).parse_and_verify(body, signature)` | local | HMAC-SHA256, hex or base64. |

## Roadmap

- **v0.1 (now)** — invoice CRUD, cryptogram charge, webhooks.
- **v0.2** — refunds, partial refunds, two-step auth/capture.
- **v0.3** — saved cards (`usercred` scope), marketplace split payouts.
- **v0.4** — sync (blocking) client mirror for non-async codebases.

## Contributing

Bug reports, feature requests, and PRs welcome — especially from anyone who has integrated Halyk and seen edge cases this SDK doesn't yet cover.

```bash
git clone https://github.com/Medeeet/halyk-epay
cd halyk-epay
pip install -e '.[dev]'
pytest && ruff check . && mypy src
```

## Disclaimer

This is an **unofficial** community library. Not affiliated with or endorsed by Halyk Bank JSC. Endpoint URLs and request schemas are based on publicly observed integrations; verify against your merchant cabinet before going to production.

## License

MIT — see [LICENSE](./LICENSE).

---

# Русская версия

Асинхронный Python SDK для **Halyk Bank ePay** — hosted page, криптограмма, вебхуки. Полностью типизирован, модели на Pydantic v2, без магии.

## Зачем

Каждый KZ-маркетплейс, интернет-магазин и финтех-проект рано или поздно интегрирует Halyk ePay — и каждый раз заново пишет одни и те же блоки `httpx.post(...)`. Эта библиотека выносит проверенный паттерн в маленький, протестированный пакет.

- **Один клиент, три сценария:** hosted page, криптограмма (direct API), вебхуки.
- **Асинхронный по умолчанию.** Встраивается в FastAPI / Starlette / aiohttp без thread pool.
- **Всё типизировано.** Pydantic v2 модели для запросов/ответов, `mypy --strict` в CI.
- **Production-grade auth.** OAuth-токены кэшируются с leeway, обновляются при 401, ретраи на 5xx с экспоненциальным backoff.
- **Честная безопасность вебхуков.** HMAC-SHA256 верификация с constant-time compare; задокументирован и распространённый кейс, когда у мерчанта подпись не включена.

## Установка

```bash
pip install halyk-epay
```

Требуется Python 3.10+.

## Быстрый старт

### Hosted Payment Page

```python
import asyncio
from halyk_epay import HalykClient, InvoiceCreate


async def main():
    async with HalykClient(
        client_id="...",
        client_secret="...",
        shop_id="...",
        environment="test",
    ) as halyk:
        invoice = await halyk.invoices.create(
            InvoiceCreate(
                invoice_id="ord-001",
                account_id="user-42",
                amount=10_000,
                currency="KZT",
                description="Заказ №001",
                back_link="https://shop.kz/return",
                failure_back_link="https://shop.kz/failure",
                post_link="https://shop.kz/halyk-webhook",
            )
        )
        print(invoice.invoice_url)  # редирект пользователя сюда


asyncio.run(main())
```

### Тестовая песочница Halyk

- **Карта:** `4405639704015096`, срок `01/27`, CVC `321`
- **Terminal id:** `67e34d63-102f-4bd1-898e-370781d0074d`
- **Публичный RSA-ключ:** [`https://test-epay-api.epayment.kz/public.rsa`](https://test-epay-api.epayment.kz/public.rsa)

Передайте `environment="test"` в `HalykClient` и `CryptogramBuilder` — попадёте на песочницу.

## Дисклеймер

Это **неофициальная** community-библиотека, не аффилирована с АО «Народный Банк Казахстана». URL'ы эндпоинтов и схемы запросов основаны на наблюдаемых интеграциях; перед продом сверьтесь с вашим личным кабинетом мерчанта.

## Лицензия

MIT.
