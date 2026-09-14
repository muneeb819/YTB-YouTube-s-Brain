# OpenAI Adapter

The optional cloud adapter uses the official OpenAI Python SDK and Responses API.
Configure `OPENAI_API_KEY` and `OPENAI_MODEL` (default `gpt-4o-mini`), then set
`AI_PROVIDER=openai`.

The rest of YTB does not depend on OpenAI, so local Ollama operation remains available.