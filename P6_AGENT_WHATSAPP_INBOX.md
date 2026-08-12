# P6 — Agent WhatsApp Inbox + Lead Capture

P6 adds a persistent, provider-neutral inbox layer for agent/customer conversations.

## Flow

Customer WhatsApp message → `/api/p6/inbound` → customer lookup/create → inbox thread/message → lead lookup/create → intent classification → agent-linked lead message.

Supported initial intents: `quote_request`, `document_intake`, `renewal`, `claim`, `general`.

## Documents

`POST /api/p6/documents` stores document metadata and optional extracted content/status. OCR is intentionally represented as a status boundary; P6 does not claim that OCR is complete until a later OCR provider patch is integrated and validated.

## Quote preparation

`POST /api/p6/quote-prepare` connects an agent/customer/lead to the existing repository `calc_quote()` function after required fields are present. The response explicitly states that authoritative provider premium/issuance must come from the approved provider integration layer.

## Preservation

Legacy Interakt/Twilio webhooks and `app.py` are not rewritten. Provider-specific webhooks can later normalize into `/api/p6/inbound` after signature validation at the adapter layer.

## Privacy/security

Persist only the minimum data required for the workflow, retain source/provider identifiers for reconciliation, and require provider/webhook authentication before using P6 inbound in production.
