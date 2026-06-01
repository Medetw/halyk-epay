# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-06-01
### Added
- Async `HalykClient` with OAuth `client_credentials` flow and in-memory token caching.
- `invoices.create()` — hosted payment page flow (returns `invoice_url`).
- `invoices.get()` — invoice status lookup.
- `payments.charge()` — cryptogram (direct API) flow.
- `cryptogram.build()` — RSA-PKCS1v15 encryption helper using Halyk's public RSA key.
- `WebhookParser` — parses Halyk `postLink` callbacks into typed `WebhookEvent`.
- `WebhookVerifier` — optional HMAC-SHA256 signature verification for merchants who enable signed callbacks.
- Pydantic v2 models for all requests/responses.
- Examples: hosted page, cryptogram charge, FastAPI webhook handler.
