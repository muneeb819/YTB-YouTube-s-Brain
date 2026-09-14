from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .auth import ensure_admin
from .config import settings
from .routes_auth import router as auth_router
from .routes_projects import router as project_router
from .routes_media import router as media_router
from .routes_jobs import router as jobs_router
from .routes_ai import router as ai_router

app = FastAPI(title="YTB — YouTube's Brain", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    ensure_admin()

@app.get("/health")
def health():
    return {"status": "ok", "service": "ytb", "ai_provider": settings.ai_provider}

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(project_router, prefix="/api/projects", tags=["projects"])
app.include_router(media_router, prefix="/api/media", tags=["media"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
