# P15 — Priya Insurance AI Core

P15 establishes a persistent, auditable AI skill layer around the existing PartnersHub application.

## Skills
- Document intake
- Quote assistant
- Renewal chaser
- Agent coach
- RM coach
- Prospect research
- Policy comparator
- Claim intake

## Knowledge
Approved knowledge sources are stored with source type, URI, status and version. The AI layer must remain source-grounded for insurance answers and must not invent insurer pricing or policy terms.

## Recommendations
AI recommendations are persisted with priority, action, reason, suggested message, source IDs and outcome state. RM-only information, including the internal ₹5,00,000 RM target, must never be exposed to an individual agent.

## Runtime
P15 is registered additively after P14 and preserves all existing legacy routes.

## Migration
P15 database objects use Alembic revision `0009_p15_priya_ai_core`, which revises `0008_p14_adaptive_agent_targets`.

## Delivery boundary
P15 can queue an approved recommendation message for the existing P8 dispatcher. Actual WhatsApp delivery remains provider-dependent and must use the P8 delivery status lifecycle.
