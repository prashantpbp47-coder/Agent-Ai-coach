# P11 — Automation + BI Foundation

P11 provides a persistent automation-run boundary and RM daily BI snapshot layer.

## Automation

`POST /api/p11/run`

Supported runs:
- `renewal_reminders` — evaluates open renewals due within 15 days and creates deduplicated 15/5/1-day reminder records.
- `followups` — marks due follow-up work as due and records an automation event.
- `message_queue` — promotes queued daily agent messages to `ready_for_dispatch` for the P8 provider dispatcher.

Runs use a unique run key so the same logical scheduler invocation is idempotent.

## BI

`POST /api/p11/bi/snapshot`

Creates/updates a persistent RM daily snapshot including actual/projected premium, renewal/new-business premium, active agents, meetings, calls, pending follow-ups and the configured ₹5 lakh target.

`GET /api/p11/bi/dashboard`

Returns the latest 30 daily snapshots for the current RM scope.

## Production boundary

P11 is the scheduler/BI foundation. A real external scheduler (cron, worker, or platform scheduler) must invoke `/api/p11/run` in production. P11 does not claim a message was delivered; P8 remains the provider delivery authority.
