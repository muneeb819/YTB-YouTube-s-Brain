# YTB — YouTube's Brain v2

## Local-First Runtime

A FastAPI-based, local-first runtime for inspecting media, generating original production
briefs through a local (or optional cloud) LLM, and producing deterministic FFmpeg renders.

- FastAPI backend with lifespan-managed startup
- JWT authentication + bcrypt password hashing
- User registration and an auto-created initial admin
- SQLite database by default, PostgreSQL-ready
- Local/offline LLM adapter through Ollama
- Optional OpenAI Responses API adapter
- Real FFmpeg media inspection (ffprobe) and rendering
- Upload/project management with configurable size caps
- Background job execution with interrupt recovery
- Rights/policy preflight gate (PASS / REVIEW / REPAIR / BLOCK)
- Render and source download endpoints
- Docker Compose deployment
- Local-first configuration

## Runtime requirements

### Local machine

- Python 3.12+
- FFmpeg available on PATH (for upload probing and rendering)
- Optional: Ollama + a locally downloaded chat model for offline AI

### Docker

```
docker compose up -d --build
```

The API runs on port 8000.

## Setup

```
cp .env.example .env    # then edit secrets
pip install -r requirements.txt
uvicorn ytb.main:app --host 0.0.0.0 --port 8000
```

Windows users can run `.\run_local.ps1`; Linux/macOS can use `./run_local.sh`.

## First login

Set `YTB_ADMIN_EMAIL` and `YTB_ADMIN_PASSWORD` (or in `.env`). The API creates the
initial admin user on startup and logs a warning if you keep the default credentials.

Additional users can be created later via `POST /api/auth/register`.

## AI providers

`AI_PROVIDER=ollama` is the default for local/offline operation.

For Ollama:

- install Ollama locally
- pull a compatible model
- set `OLLAMA_MODEL`

For OpenAI:

- set `AI_PROVIDER=openai`
- set `OPENAI_API_KEY`
- set `OPENAI_MODEL` (default `gpt-4o-mini`)

OpenAI is optional. The core app does not require an OpenAI key.

## API quick reference

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/api/auth/register` | Create a normal user |
| POST | `/api/auth/login` | Get a bearer token |
| GET | `/api/auth/me` | Current user |
| POST | `/api/projects` | Create a project |
| GET | `/api/projects` | List owned projects |
| GET | `/api/projects/{id}/preflight` | Rights preflight summary |
| POST | `/api/media/upload/{project_id}` | Upload a media asset (probed with ffprobe) |
| POST | `/api/media/{asset_id}/rights` | Set `COMPLIANT`/`BLOCKED`/`UNKNOWN` |
| GET | `/api/media/{asset_id}/download` | Download the source asset |
| POST | `/api/jobs/render` | Queue a deterministic FFmpeg trim render |
| GET | `/api/jobs/{id}` | Job status/output |
| GET | `/api/jobs/{id}/download` | Download the completed render |
| POST | `/api/ai/generate` | Generate text via the configured provider |
| GET | `/health` | Liveness + active AI provider |

Rendering is gated by the rights preflight: assets marked `BLOCKED` return `403`.

## Tests

```
pip install -r requirements.txt
pytest
```

The suite uses an isolated temporary SQLite database and exercises auth, projects,
uploads, rights/preflight, render validation and job lifecycle.

## Important safety boundary

YTB is a risk-reduction system. It does not and cannot guarantee zero copyright claims,
strikes, takedowns, Content ID actions, or monetization decisions. It does not implement
Content ID/enforcement evasion, false seconds/percentage copyright rules, fabricated rights
evidence, or similar bypasses.

## What is functional now

1. Authenticate (login, register, JWT).
2. Create a project.
3. Upload a video (with a configurable size cap and ffprobe inspection).
4. Inspect it via FFprobe.
5. Ask the configured local/cloud model to generate an original production brief/script.
6. Create a deterministic FFmpeg render from a source video with optional start/end trim.
7. Store jobs, assets and outputs in SQLite.
8. Run a rights/policy preflight per asset and per project (PASS / REVIEW / REPAIR / BLOCK).
9. Download the source asset and the resulting render.

## Not yet implemented

Advanced scene detection, OCR, high-quality transcription, voice cloning/TTS, thumbnail
generation, semantic visual selection, a React/Vite control center and YouTube OAuth remain
adapter points rather than being represented as complete production-grade features.