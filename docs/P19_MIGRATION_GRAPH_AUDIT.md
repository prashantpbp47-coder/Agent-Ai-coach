# P19 Migration Graph Audit

Status: AUDIT COMPLETE — REPAIR REQUIRED BEFORE P19 MIGRATION

## Verified revision graph

- `0001_p0_foundation` → `0002_p4_rm_operations`
- `0002_p4_rm_operations` → `0003_p5_rm_visits_referrals`
- `0002_p4_rm_operations` → `0003_p6_agent_inbox`
- `0003_p6_agent_inbox` → `0004_p8_messaging_delivery`
- `0004_p8_messaging_delivery` → `0005_p9_document_intelligence`
- `0004_p9_document_intelligence.py` filename is legacy/misleading; its actual revision is `0005_p9_document_intelligence`
- `0005_p9_document_intelligence` → `0005_p10_followup_renewal` is NOT the declared relationship; `0005_p10_followup_renewal` currently declares `0004_p9_document_intelligence`, which does not exist as a revision ID.
- `0005_p10_followup_renewal` → `0006_p11_automation_bi`
- `0005_p10_followup_renewal` → `0006_p12_clay_prospect_intelligence`
- `0006_p12_clay_prospect_intelligence` → `0007_p13_bi_reconciliation`
- `0007_p13_bi_reconciliation` → `0008_p14_adaptive_agent_targets`
- `0008_p14_adaptive_agent_targets` → `0009_p15_priya_ai_core`
- `0009_p15_priya_ai_core` → `0010_p16_provider_calls`
- `0010_p16_provider_calls` → `0011_p18_campaign_automation`

## Confirmed inconsistencies

1. `0004_p7_rm_targets_marketing.py` declares `revision = "0004_p7"` and `down_revision = "0003_p6"`, but no revision named `0003_p6` is present in the repository. The actual P6 revision is `0003_p6_agent_inbox`.
2. `0004_p9_document_intelligence.py` has a filename suggesting `0004`, but declares `revision = "0005_p9_document_intelligence"`.
3. `0005_p10_followup_renewal.py` declares `down_revision = "0004_p9_document_intelligence"`, which does not exist as an actual revision ID; the P9 file declares `0005_p9_document_intelligence`.
4. P11 and P12 both branch from `0005_p10_followup_renewal`. P13 follows only P12, leaving P11 as a separate head unless it is intentionally joined elsewhere.
5. P5 branches from P4 while the operational P6/P8/P9 chain follows the other P4 child. This is a legitimate branch only if the migration graph later joins it; no join was found in the inspected chain.

## Decision

Do not create a P19 migration until these graph inconsistencies are resolved safely. Do not delete or rewrite historical migrations. The repair should use explicit compatibility/merge revisions or another Alembic-safe strategy after reviewing the deployed database revision state.

## P19 requirement

P19 needs a new migration only after a valid migration head/merge point is established. The P19 application code remains unchanged by this audit document.
