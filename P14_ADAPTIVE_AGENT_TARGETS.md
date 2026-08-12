# P14 — Adaptive Agent Targets + AI Follow-up

## Business rule
- RM's overall ₹5 lakh target is an internal RM metric and is not displayed to individual agents.
- Each agent receives an individualized daily target based on back-record performance, activation status, and club/tier assignment.
- New/re-activation baseline starts at ₹1,000.
- Successful agents can receive higher targets; ₹19,000 is the default Smart Agent tier benchmark unless a configured club target overrides it.
- Club-member targets remain configurable per club/tier.

## AI follow-up
Recommendations use target gap, recent business, activity/contact state, follow-up due state and agent tier to suggest the next action and message. Recommendations are advisory and must remain auditable.

## Visibility
Agent-facing endpoints expose only that agent's own target/progress. RM endpoints can see the individual target plans and aggregate progress, including the hidden RM total target.

## Safety
The engine must never expose the RM's ₹5 lakh target to an agent through API responses, WhatsApp templates, Priya messages or referral pages.
