# YTB — YouTube's Brain v2
## Fully Functional Local-First Runtime

This version adds real runtime components to the earlier scaffold:

- FastAPI backend
- JWT authentication + password hashing
- SQLite database by default, PostgreSQL-ready
- Local/offline LLM adapter through Ollama
- Optional OpenAI Responses API adapter
- Real FFmpeg media inspection and rendering
- Upload/project management
- Background job execution
- Policy/rights safety gate
- Persistent job state
- React/Vite control center
- Docker Compose deployment
- Local-first configuration

## Runtime requirements

### Local machine
- Python 3.12+
- FFmpeg available on PATH
- Optional: Ollama + a locally downloaded chat model for offline AI
- Node 20+ only if running the web UI outside Docker

### Docker
`docker compose up -d --build`

The API runs on port 8000 and the web UI on port 3000.

## First login
Set:
- `YTB_ADMIN_EMAIL`
- `YTB_ADMIN_PASSWORD`

The API creates the initial admin user on startup.

## AI providers

`AI_PROVIDER=ollama` is the default for local/offline operation.

For Ollama:
- install Ollama locally
- pull a compatible model
- set `OLLAMA_MODEL`

For OpenAI:
- set `AI_PROVIDER=openai`
- set `OPENAI_API_KEY`
- set `OPENAI_MODEL`

OpenAI is optional. The core app does not require an OpenAI key.

## Important safety boundary

YTB is a risk-reduction system. It does not and cannot guarantee zero copyright claims,
strikes, takedowns, Content ID actions, or monetization decisions. It does not implement
Content ID/enforcement evasion, false seconds/percentage copyright rules, fabricated rights
evidence, or similar bypasses.

## What is functional now

1. Authenticate.
2. Create a project.
3. Upload a video.
4. Inspect it with FFprobe/FFmpeg.
5. Ask the configured local/cloud model to generate an original production brief/script.
6. Create a deterministic FFmpeg render from a source video with optional start/end trim.
7. Store jobs, assets and outputs in SQLite.
8. Run a rights/policy preflight that can PASS/REPAIR/BLOCK.
9. Download the resulting render.

Advanced scene detection, OCR, high-quality transcription, voice cloning/TTS, thumbnail
generation, semantic visual selection and YouTube OAuth remain adapter points rather than
being falsely represented as complete production-grade features.
