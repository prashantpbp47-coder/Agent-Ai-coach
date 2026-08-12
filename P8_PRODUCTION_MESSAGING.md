# P8 — Production Messaging Dispatcher

P8 promotes the P7 daily-agent message queue into a provider-aware delivery lifecycle without rewriting legacy `app.py`, Interakt webhooks, or Twilio voice routes.

## Delivery lifecycle

`queued -> sent -> delivered/read` or `failed -> retry (max 3)`.

P8 stores provider references, timestamps, errors, attempts and callback payloads.

## Providers

- `interakt`: uses `INTERAKT_API_KEY` (or existing `INTERAKT_KEY`).
- `twilio`: uses `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, and optionally `TWILIO_MESSAGE_STATUS_CALLBACK`.

P8 does not report delivery merely because an API request was queued. A provider reference is stored first, then callbacks update final delivery state where supported.

## APIs

- `POST /api/p8/dispatch` — dispatch queued daily messages.
- `POST /api/p8/consent/<agent_id>` — update agent messaging opt-out state.
- `POST /api/p8/status/twilio` — receive Twilio delivery callbacks.
- `POST /api/p8/retry` — retry failed messages whose retry time has arrived.

## Operational requirements

1. Configure the provider credentials as environment secrets.
2. Configure and verify the provider callback URL before treating delivered/read as production-trusted.
3. Schedule `/api/p8/dispatch` through a trusted scheduler/worker rather than exposing an unauthenticated public trigger.
4. Respect agent opt-out state.
5. Keep P7's daily dedupe key as the business-level duplicate protection.

## Current verification boundary

Static repository validation is complete. Live Interakt delivery and Twilio callback delivery require deployed credentials and webhook configuration.
