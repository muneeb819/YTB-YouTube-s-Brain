import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import ensure_admin
from .config import settings
from .db import init_db
from .jobs import recover_interrupted_jobs
from .routes_ai import router as ai_router
from .routes_auth import router as auth_router
from .routes_jobs import router as jobs_router
from .routes_media import router as media_router
from .routes_projects import router as project_router

logger = logging.getLogger("ytb.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_admin()
    recover_interrupted_jobs()
    if settings.ytb_secret_key == "change-me" or settings.ytb_admin_password == "change-me":
        logger.warning(
            "YTB is running with default credentials/secret. "
            "Set YTB_SECRET_KEY and YTB_ADMIN_PASSWORD before any non-local deployment."
        )
    yield


app = FastAPI(title="YTB — YouTube's Brain", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ytb", "ai_provider": settings.ai_provider}


@app.get("/api/health", include_in_schema=False)
def health_api():
    return {"status": "ok", "service": "ytb", "ai_provider": settings.ai_provider}


app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(project_router, prefix="/api/projects", tags=["projects"])
app.include_router(media_router, prefix="/api/media", tags=["media"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])