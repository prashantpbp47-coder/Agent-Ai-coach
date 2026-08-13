# P15 — Priya Insurance AI Core

P15 establishes a provider-neutral insurance AI skill layer around the existing legacy Priya/OpenAI implementation.

## Skills
- Document Intake
- RC Reader
- Quote Assistant
- Renewal Chaser
- Agent Coach
- RM Coach
- Prospect Research
- Policy Comparator
- Claim Intake
- Knowledge Answer

## Core behavior
- Approved insurance knowledge is stored with source metadata.
- Knowledge search returns matching source excerpts rather than inventing unsupported answers.
- P14 individualized agent targets are the business-control input for Agent Coach recommendations.
- RM's internal ₹5 lakh total target is never exposed to agent-facing endpoints or suggested messages.
- Recommendations can be placed into the existing P7 WhatsApp message queue with per-recommendation/day deduplication.
- AI tasks are persisted for provider-specific execution later.

## Human control
P15 recommendations are advisory. It does not invent insurer prices, policy issuance outcomes, underwriting decisions or claim decisions.

## Next integration
The next AI integration should connect the existing OpenAI implementation to P15 tasks while retaining an auditable provider boundary and allowing a future DeepSeek fallback.
