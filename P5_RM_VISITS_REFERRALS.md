# P5 — RM Visit Planner, Area Intelligence & Agent Referral

## Operating rule
Each RM gets a daily 5-meeting plan:
- 3 existing agents
- 2 new-agent prospects

A plan is generated for today and can also be generated for a future date (for example tomorrow). Existing agents are preferred from the same requested area when area is supplied. New prospects are selected from candidate records in the same area when available.

## Prospecting
Prospects can be entered from approved/public research sources, referrals, inbound messages, or other compliant sources. Store source URL/evidence and consent/contact status. The system is intentionally not a private-data scraper.

## Referral links
Every agent can have one durable, unique referral slug. A public `/r/<slug>` route tracks clicks and can redirect to an explicitly configured HTTPS destination. Referral attribution can create a customer/lead tied to the originating agent.

Internal attribution is guaranteed by PartnersHub data. Official insurer/PBPartners policy attribution must be confirmed by an approved integration contract/API; the system must not represent an unverified external attribution as confirmed.

## Main APIs
- `POST /api/p5/visit-plan/generate`
- `GET /api/p5/visit-plan`
- `POST /api/p5/prospects`
- `GET /api/p5/prospects`
- `POST /api/p5/referral-links`
- `GET /api/p5/referral-links/<agent_id>`
- `POST /api/p5/referral-links/<agent_id>/deactivate`
- `POST /api/p5/referral-attribution`
- Public redirect/tracking: `/r/<slug>`

## Dependencies
Run `alembic upgrade head` after deployment. P5 depends on P0-P4 database tables, authentication and RBAC.
