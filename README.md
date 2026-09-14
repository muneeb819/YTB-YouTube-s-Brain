# YTB — YouTube's Brain v2

A local-first, monorepo runtime for inspecting media, generating original production
briefs via a local/optional cloud LLM, and producing deterministic FFmpeg renders.

```
YTB-YouTube-s-Brain/
├── backend/       FastAPI API + background renderer + SQLite store
├── frontend/      React + Vite control-center UI (TypeScript, plain CSS)
└── docker-compose.yml
```

## Features

- FastAPI backend with lifespan-managed startup
- JWT authentication + bcrypt password hashing
- User registration and auto-created initial admin
- SQLite default, PostgreSQL-ready
- Local/offline LLM adapter through Ollama + optional OpenAI adapter
- Real FFmpeg media inspection (ffprobe) and rendering with stream-copy fallback
- Upload/project management with configurable size caps
- Background job execution with interrupt recovery
- Rights/policy preflight gate (PASS / REVIEW / REPAIR / BLOCK)
- Render and source download endpoints
- React/Vite control-center UI: auth, projects, upload, rights, preflight, renders, downloads
- Docker Compose deployment (api + nginx-served frontend)

## Runtime requirements

### Local

- Python 3.12+
- Node.js 18+ (for the frontend)
- FFmpeg on PATH (or set `FFMPEG_BIN` / `FFPROBE_BIN` env vars)
- Optional: Ollama + a downloaded chat model for offline AI

### Docker

```bash
docker compose up -d --build
```

The API is on port `8000`, the frontend (nginx) on port `3000`.

## Backend setup

```bash
cd backend
cp .env.example .env    # edit secrets / CORS_ORIGINS
pip install -r requirements.txt
uvicorn ytb.main:app --host 0.0.0.0 --port 8000
```

Windows: `.\run_local.ps1` | Linux/macOS: `./run_local.sh`

## Frontend setup

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api → localhost:8000)
```

For a production build served by nginx alongside the API:

```bash
cd frontend && npm run build    # output in frontend/dist
docker compose up -d --build    # builds api + nginx web service
```

## First login

Set `YTB_ADMIN_EMAIL` and `YTB_ADMIN_PASSWORD` (or in `.env`). The API creates the
initial admin on startup and logs a warning if default credentials are kept.

New accounts can be created via `POST /api/auth/register`.

## AI providers

`AI_PROVIDER=ollama` is the default for local/offline operation.

- **Ollama**: install locally, pull a model, set `OLLAMA_MODEL`.
- **OpenAI**: set `AI_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-4o-mini`).

OpenAI is optional. The core app does not require an OpenAI key.

## API quick reference

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/health` | Liveness + active AI provider |
| POST | `/api/auth/register` | Create a normal user |
| POST | `/api/auth/login` | Get a bearer token |
| GET | `/api/auth/me` | Current user |
| POST | `/api/projects` | Create a project |
| GET | `/api/projects` | List owned projects |
| GET | `/api/projects/{id}/assets` | List uploaded assets for a project |
| GET | `/api/projects/{id}/jobs` | List render jobs for a project |
| GET | `/api/projects/{id}/preflight` | Rights preflight summary |
| POST | `/api/media/upload/{project_id}` | Upload a media asset |
| POST | `/api/media/{asset_id}/rights` | Set `COMPLIANT` / `BLOCKED` / `UNKNOWN` |
| GET | `/api/media/{asset_id}/download` | Download the source asset |
| POST | `/api/jobs/render` | Queue a deterministic FFmpeg trim render |
| GET | `/api/jobs/{id}` | Job status/output |
| GET | `/api/jobs/{id}/download` | Download the completed render |
| POST | `/api/ai/generate` | Generate text via the configured provider |

All `/api/*` routes (except `register` / `login`) require a `Bearer` token.

Rendering is gated by the rights preflight: assets marked `BLOCKED` return `403`.

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

The suite uses an isolated temporary SQLite database and covers auth, projects,
uploads, rights/preflight, asset/job listing, render validation and job lifecycle.

## Safety

YTB is a risk-reduction system. It does not and cannot guarantee zero copyright claims,
strikes, takedowns, Content ID actions, or monetization decisions.

## What is functional

1. Authenticate (login, register, JWT).
2. Create a project.
3. Upload a video (with a size cap and ffprobe inspection).
4. Inspect assets via FFprobe.
5. Generate an original production brief via a local or cloud LLM.
6. Set asset rights status and run a rights/policy preflight per project.
7. Create a deterministic FFmpeg render with stream-copy or re-encode fallback.
8. Store jobs, assets and outputs in SQLite.
9. Download source assets and resulting renders.
10. React/Vite control-center UI covering the full workflow.

## Not yet implemented

Advanced scene detection, OCR, high-quality transcription, voice cloning/TTS, thumbnail
generation, semantic visual selection, and YouTube OAuth remain adapter points rather
than being represented as complete production-grade features.