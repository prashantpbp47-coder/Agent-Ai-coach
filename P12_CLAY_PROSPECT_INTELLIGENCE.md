# P12 — Clay Prospect Intelligence

P12 makes Clay an optional external prospect-research source while PartnersHub remains the CRM/source of truth.

## Flow

Clay/public prospect research → P12 ingestion → dedupe/update AgentProspect → intelligence score → RM recommended prospects → P5 2-new-agent daily meeting slots.

## APIs

`POST /api/p12/clay/import` accepts a provider-neutral list of prospect rows exported or delivered from Clay. It does not require a Clay API subscription.

`GET /api/p12/prospects/recommended?area=<area>` returns the highest-scoring prospects for the current RM/area.

`GET /api/p12/health` reports provider-boundary status.

## Scoring

The initial deterministic score considers area fit, profession fit, public/source evidence, business-potential hints and relationship context. It is deliberately transparent and can later be replaced/augmented by Priya AI without changing the CRM contract.

## Cost boundary

Clay's current Free plan includes 500 actions/month and 100 data credits/month, plus prospecting/list-building and Claygent research. Paid HTTP API integration/webhook automation is not assumed for P12; the platform can ingest CSV/exported results or another approved integration. Clay's pricing and documentation should be rechecked before activating any paid automation.

## Privacy and outreach

Store source URL/evidence and consent/contact status. Do not scrape or use private personal contact details without an appropriate lawful/consensual basis. RM remains the human relationship owner.
