# P16 AI Provider Layer

Providers: OpenAI and DeepSeek.

Environment variables: OPENAI_API_KEY, OPENAI_MODEL, DEEPSEEK_API_KEY, DEEPSEEK_MODEL, AI_PROVIDER, AI_FALLBACK_PROVIDER, AI_TIMEOUT_SECONDS.

The provider router records provider, model, HTTP status, latency, token usage and errors in ai_provider_calls.

DeepSeek uses the official OpenAI-compatible endpoint. Current production model defaults should be reviewed before deployment.

RM-only context must not expose the hidden RM aggregate target to an Agent.
