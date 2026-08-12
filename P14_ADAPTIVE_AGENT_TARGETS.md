# P14 — Adaptive Agent Targets + AI Follow-up

## Business rule
- RM's overall ₹5 lakh target is an internal RM metric and is never shown to individual agents.
- Each agent receives an individualized daily target based on recent/back-record business, activation status and optional club/tier rules.
- Inactive or reactivation agents start at ₹1,000.
- Successful agents can move into the Smart Agent tier with a ₹19,000 benchmark; club rules can override the benchmark within the configured ₹1,000–₹2,00,000 range.
- Agent-facing APIs expose only the individual target/progress.

## AI-assisted follow-up
P14 creates auditable next-best-action recommendations from target gap, recent performance and tier. It supplies a suggested message/follow-up time; P8 remains responsible for actual WhatsApp/Twilio delivery.
