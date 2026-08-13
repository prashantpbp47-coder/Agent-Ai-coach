# P16 — OpenAI + DeepSeek Provider Layer

P16 adds a provider-neutral reasoning layer for Priya AI.

## Provider selection

- `AI_PROVIDER=openai` or `AI_PROVIDER=deepseek`
- `AI_FALLBACK_PROVIDER=deepseek` (optional)
- `OPENAI_API_KEY` / `OPENAI_MODEL` for OpenAI Responses API
- `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` for DeepSeek OpenAI-compatible Chat Completions
- `AI_TIMEOUT_SECONDS` defaults to 30

No provider secret is stored in the repository or database.

## Safety boundaries

- Agent-facing reasoning receives only that agent's permitted target/history context.
- RM-only aggregate targets are never included in agent prompts.
- Priya must not invent insurer pricing, policy eligibility, or official policy issuance status.
- Knowledge-grounded answers cite the supplied knowledge-source IDs in the stored audit record.
- Provider failure never silently fabricates an answer; the task remains retryable/failed.

## APIs

- `POST /api/p16/reason` — authenticated AI reasoning task.
- `GET /api/p16/health` — provider configuration health without exposing secrets.

## Environment

```text
AI_PROVIDER=openai
AI_FALLBACK_PROVIDER=deepseek
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-flash
AI_TIMEOUT_SECONDS=30
```

OpenAI uses the Responses API. DeepSeek uses its OpenAI-compatible endpoint at `https://api.deepseek.com/chat/completions`.
