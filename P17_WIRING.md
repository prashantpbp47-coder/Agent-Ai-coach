# P17 Wiring

P17 Priya-to-messaging automation is registered in `foundation/__init__.py` and should be included by `p0_runtime.py` before deployment. The P17 blueprint delegates delivery to the existing P8 dispatcher so consent, retries, and provider delivery status remain centralized.

Runtime validation checklist:
- `/api/p17/agent-coach/queue`
- `/api/p17/dispatch`
- P8 provider delivery state
- agent-facing target context excludes RM aggregate target
- daily dedupe key prevents duplicate coaching messages
