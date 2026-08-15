# P13 — BI + Business Reconciliation

P13 makes reporting source-aware without overwriting the PartnersHub business ledger.

## External business import

`POST /api/p13/business/import`

Accepts normalized source rows with:
- source_name
- source_reference
- category
- agent_code
- policy_reference
- premium
- policies
- import_date

Import rows remain identifiable and deduplicated by RM/source/reference/policy reference.

## Reconciliation

`POST /api/p13/reconcile`

Compares external source totals against `BusinessEvent` totals for the same RM/date/source and produces total and category-level differences.

Status is `matched` only when premium and policy differences are within the supplied tolerances.

`GET /api/p13/reconciliation`

Lists reconciliation runs for the RM/date.

## Daily RM report

`POST /api/p13/daily-report`

Builds a persistent RM report containing actual/projected premium, ₹5L target, active agents, calls, meetings, high-value agents and reconciliation mismatches.

`GET /api/p13/agent-performance`

Returns agent-level daily premium, policy count and category breakdown.

## Source-of-truth rule

PartnersHub remains the operational CRM/source ledger. External imports are evidence for reconciliation and do not automatically alter internal business totals.

Final external/PBPartners integration remains provider-contract dependent; P13 supports normalized import so a future approved API/CSV/report connector can feed it without changing reporting logic.
