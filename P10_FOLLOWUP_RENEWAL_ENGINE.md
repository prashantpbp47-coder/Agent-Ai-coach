# P10 — Follow-up and Renewal Engine

P10 adds persistent renewal and follow-up workflows without rewriting the legacy Flask application.

## Renewal cadence
- 15 days before expiry
- 5 days before expiry
- 1 day before expiry

Each renewal creates deduplicated reminder records for agent and customer channels. Delivery remains provider-controlled and can be connected to the P8 dispatcher.

## Follow-up workflow
- Persistent tasks with due time, priority and ownership
- Due-task queue for Agent/RM/Master Agent/Admin
- Completion records and follow-up events
- Optional next follow-up creation

## Renewal dashboard
RM dashboard exposes renewals total, 15/5/1-day due buckets, open follow-ups, renewed count and renewed premium.

## Important boundary
P10 queues and tracks workflow state. It does not claim that a WhatsApp reminder was delivered until the P8/provider delivery layer reports that state.

## Migration
Run `alembic upgrade head`. P10 migration follows `0004_p9_document_intelligence`.

## Next
P11 should connect P10 reminders to the P8 dispatcher, add automated scheduling/worker execution, and reconcile renewal premium into the RM ₹3L–₹5L daily target and BI layer.
