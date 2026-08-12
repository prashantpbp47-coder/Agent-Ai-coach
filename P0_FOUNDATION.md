# PartnersHub AI — P0 Foundation Lock

This patch adds the first persistent platform foundation without deleting or rewriting the legacy Priya AI implementation.

## What P0 adds

- Flask-SQLAlchemy persistence foundation
- PostgreSQL support through `DATABASE_URL`
- Alembic migration framework
- User authentication with JWT access tokens
- Password hashing using Werkzeug
- RBAC roles: `AGENT`, `RM`, `MASTER_AGENT`, `ADMIN`
- Baseline permissions for core CRM/insurance domains
- Persistent master tables for agents, RMs, customers, leads, quotes, policies, renewals and follow-ups
- AI conversation and audit-log tables
- P0 health endpoint
- One-time admin bootstrap endpoint
- Runtime wrapper that preserves the existing `app.py` routes

## Runtime

The Procfile now runs `p0_runtime:app`. That module imports the existing `app:app` first and then attaches the P0 foundation. Existing Priya/Twilio/Interakt routes are therefore retained rather than replaced.

## Database migration

Set `DATABASE_URL`, then run:

```bash
alembic upgrade head
```

For local-only testing, Alembic falls back to `sqlite:///partnershub_p0.db`.

## Required production secrets

Set:

- `DATABASE_URL`
- `JWT_SECRET_KEY` — at least 32 characters
- `P0_BOOTSTRAP_TOKEN` — long random deployment secret

Existing OpenAI, Interakt and Twilio secrets remain environment-driven.

## Bootstrap the first administrator

POST `/api/p0/auth/bootstrap` with header `X-P0-Bootstrap-Token` and JSON containing:

```json
{
  "email": "admin@example.com",
  "full_name": "Platform Admin",
  "password": "a-strong-password-at-least-12-chars",
  "phone": "+91XXXXXXXXXX"
}
```

The endpoint is one-time only: it refuses to create an administrator once any user exists.

## Authentication

POST `/api/p0/auth/login` with email/password to obtain a JWT. Send it on protected endpoints as:

`Authorization: Bearer <token>`

## Important non-goals

P0 does not claim that insurer quotation APIs, OCR, DeepSeek, BI, forecast, NBA, self-healing, backup, rollback, or full CRM workflows are complete. Those remain later patches.

## Compatibility rule

The legacy application remains the master reference. P0 is intentionally additive and should be extended through incremental patches rather than replacing the current application wholesale.
