# P2 — Persistent Quote Bridge

P2 connects the repository's existing `calc_quote()` logic to the P1 persistent domain layer without replacing the legacy `/quote-request` route.

## API

`POST /api/p2/quote-request`

Authentication: `Authorization: Bearer <token>`

Required permission: `quotes:write`

The endpoint calls the existing calculator, finds or creates the customer, creates a persistent Lead, creates a persistent Quote, and writes an AuditLog entry.

## Compatibility

The existing `/quote-request` endpoint remains unchanged. Migration to the persistent endpoint can therefore be incremental.

## Next

P3 should introduce insurer/provider adapter boundaries and connect PBPartners quotation links without hard-coding provider credentials into application code.
