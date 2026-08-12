# P4 — RM Command Center

P4 turns the RM workflow into a persistent operating system.

## Daily targets

Defaults are:
- 20 priority RM contacts/day
- 5 active agents/day
- 3 agents/day at or above ₹10,000 business
- ₹10,000 is configurable per RM/day

## Call queue rule

The queue is generated from the persistent agent master. An agent contacted today is excluded from the same-day queue unless the contact explicitly requires follow-up and the follow-up is due.

Priority increases for follow-up-due, never-contacted, stale-contact and activation-gap agents.

## RM actions

- `/api/rm/daily-plan` — current top priority list
- `/api/rm/contact` — store channel, outcome, remarks, follow-up and projection
- `/api/rm/dispatch` — send one call or WhatsApp message through the existing adapters
- `/api/rm/projection` — store daily projected premium/policies and active state
- `/api/rm/hierarchy` — define master-agent/sub-agent relationship
- `/api/rm/business` — record actual business by category
- `/api/rm/dashboard` — daily RM scorecard and all-agent view
- `/api/rm/reconciliation` — compare imported/external totals against PartnersHub totals
- `/api/rm/contacts/export.csv` — export the RM contact history for reporting

## Agent vs Master Agent

An agent is a direct working partner. A master agent is an agent with one or more active sub-agent relationships stored in `agent_hierarchy`. The RM remains the controlling scope.

## Business reconciliation

Business is stored as category-level events with amount, policy count, source and external reference. Daily RM reporting can therefore compare PartnersHub totals with imported PBPartners/external totals and mark the day as `matched` or `mismatch`.

## Automation boundary

The dispatch API is intentionally callable by a scheduler/automation service. Live scheduling, campaign throttling and inbound WhatsApp automation will be completed in the dedicated automation phase so that message/call policy remains centralized and auditable.
