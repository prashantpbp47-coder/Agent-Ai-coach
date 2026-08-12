# P7 — RM Daily Business Target & AI Agent Marketing

## Business rule
Each RM is measured against a daily business range of ₹3,00,000 minimum and ₹5,00,000 target. The dashboard exposes the gap and achievement. The target is configurable per RM/day.

## Agent activation engine
The existing P4 daily contact queue remains the execution layer. P7 adds the daily business target and stores queued agent messages with a unique dedupe key so the same daily message is not queued twice for the same agent/channel/type.

## Marketing strategy
Marketing plans can be stored by date, channel, segment and objective. Segments can later include active agents, inactive agents, high-value agents, new agents, renewal opportunities and product-specific campaigns. Message text supports `{{agent_name}}`, `{{target}}`, and `{{minimum}}` placeholders.

## Automatic messaging boundary
P7 queues messages persistently. Actual provider dispatch must use the approved Interakt/Twilio adapter and provider credentials. This separation prevents the target engine from silently fabricating delivery status.

## Recommended daily cadence
- Morning: target + projection request.
- Midday: gap-to-target nudge for agents without projection/business.
- Afternoon: focused conversion message for pending opportunities.
- Evening: achievement/remaining-gap reminder and next-day pipeline capture.

## Safety / compliance
Messages should be relevant to the agent's business workflow. Avoid claims about guaranteed earnings or product suitability. Final policy issuance and provider business figures must come from approved provider systems and reconciliation, not marketing messages.
