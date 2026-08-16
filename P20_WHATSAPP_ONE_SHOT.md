# P20 — WhatsApp One-Shot Quotation Orchestrator

## Purpose
Agents no longer need to answer a rigid sequence of WhatsApp questions. They can send the complete requirement in one message and upload the available documents together.

## Inbound endpoint
`POST /api/p20/whatsapp/inbound`

The webhook:
- validates the optional `X-PartnersHub-Signature` HMAC when `WHATSAPP_WEBHOOK_SECRET` is configured;
- deduplicates repeated provider message IDs;
- extracts vehicle number, customer name, email, plan, add-ons and expiry date;
- captures RC/policy attachment flags;
- merges new information into the persistent WhatsApp session;
- returns one consolidated `missing_fields` list rather than asking one question at a time;
- moves the intent to `ready_for_quote` when the required intake is complete.

## Agent experience
Example single message:

`Renew MH15AB1234. Comprehensive + Zero Dep + Engine Protect. Customer name: Prashant Chandratre. Email: prashant@example.com. RC and previous policy attached.`

The response is either:
- `ready_for_quote` → proceed to quotation preparation; or
- `collecting` → one message listing all remaining requirements.

## Storage
Migration `0015_p20_whatsapp_one_shot` adds:
- `whatsapp_sessions`
- `whatsapp_events`
- `whatsapp_quote_intents`

## Security
Configure `WHATSAPP_WEBHOOK_SECRET` in production. The intent management endpoint remains authenticated/RBAC protected.

## Next bridge
The `ready_for_quote` intent is deliberately a clean boundary for the existing quote/provider/RC-document modules. P20 does not invent insurer pricing or payment URLs; those remain provider-authoritative operations.
