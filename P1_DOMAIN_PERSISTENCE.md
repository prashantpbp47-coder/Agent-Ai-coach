# P1 — Domain Persistence

## Scope
P1 adds authenticated, persistent domain APIs without rewriting the legacy Priya AI application.

## Runtime
The existing `app.py` remains the source of legacy routes. `p0_runtime.py` attaches the P0 foundation and P1 domain blueprint.

## Persistent domains
- Agents
- RMs
- Customers
- Leads
- Quotes
- Policies
- Renewals
- Follow-ups

## API prefix
`/api/p1`

GET list endpoints require the corresponding read permission. POST endpoints require the corresponding write permission. `/api/p1/summary` requires `reports:read`.

## Legacy migration
`POST /api/p1/legacy/import` is ADMIN-only and idempotently copies the current `app.AGENTS` list into the persistent Agent table. It does not delete or alter the legacy list.

## Required deployment state
P0 migration must already be applied with `alembic upgrade head`. The application requires `DATABASE_URL` and `JWT_SECRET_KEY` as documented by P0.

## Compatibility rule
No legacy Priya AI route is removed or rewritten by P1. P1 adds persistent domain APIs alongside the existing implementation.
