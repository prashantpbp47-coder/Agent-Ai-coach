# P18 — Shared Messaging Campaign Automation

P18 extends the existing P6 inbox and P8 provider-delivery layers; it does not replace them.

## Delivered in this patch

- Persistent campaign definitions.
- Agent recipient lists with deduplication.
- Template rendering for `{{agent_name}}` and `{{partner_code}}`.
- Safe queueing into the existing `AgentDailyMessage` P7 queue.
- Campaign cancellation.
- Inbox next-action records with human-approval by default.
- Audit events for campaign and inbox-action operations.
- Alembic revision `0011_p18_campaign_automation` after P16 revision `0010_p16_provider_calls`.
- Safe P18 import/route/Gunicorn smoke workflow.

## Delivery boundary

P18 never calls Interakt/Twilio directly. It creates queued `AgentDailyMessage` records and leaves actual provider delivery to P8, preserving consent, provider status, retry and callback behavior.

## Human control

Inbox actions default to `requires_human_approval=true`. P18 does not autonomously send an AI-generated customer response merely because an inbox action exists.

## Future P18 patches

- scheduled campaign worker execution;
- segment rules based on agent status/tier/target gap;
- inbound P6 thread classification through P16/Priya;
- approval UI and message preview;
- delivery analytics and campaign-level reconciliation.

Real provider delivery and deployed database migration remain environment-dependent.
