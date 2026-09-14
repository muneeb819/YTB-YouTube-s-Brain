import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .auth import current_user
from .config import settings
from .db import get_db
from .jobs import submit_render
from .models import Job, MediaAsset, Project
from .safety import preflight

router = APIRouter()


class RenderRequest(BaseModel):
    project_id: int
    asset_id: int
    start: float = Field(0, ge=0)
    duration: float | None = Field(None, gt=0)


@router.post("/render")
def render(body: RenderRequest, user=Depends(current_user), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == body.project_id, Project.owner_id == user.id).first()
    asset = db.query(MediaAsset).filter(MediaAsset.id == body.asset_id, MediaAsset.project_id == body.project_id).first()
    if not project or not asset:
        raise HTTPException(404, "Project or asset not found")

    verdict = preflight(asset.rights_status)
    if verdict == "BLOCK":
        raise HTTPException(403, "Asset is blocked by the rights preflight")

    job = Job(
        project_id=project.id,
        type="FFMPEG_RENDER",
        state="QUEUED",
        input_json=json.dumps(body.model_dump()),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    submit_render(job.id, asset.id, body.start, body.duration)
    return {"job_id": job.id, "state": job.state}


@router.get("/{job_id}")
def get_job(job_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    project = db.get(Project, job.project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(403, "Forbidden")
    return {
        "id": job.id,
        "type": job.type,
        "state": job.state,
        "output": json.loads(job.output_json or "{}"),
        "error": job.error,
    }


@router.get("/{job_id}/download")
def download(job_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    project = db.get(Project, job.project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(403, "Forbidden")

    if job.state != "COMPLETED":
        raise HTTPException(404, "No completed output available for this job")

    output = json.loads(job.output_json or "{}")
    out_path = output.get("path")
    if not out_path:
        raise HTTPException(404, "Job has no output path")

    storage = Path(settings.ytb_storage_dir).resolve()
    try:
        resolved = Path(out_path).resolve()
        resolved.relative_to(storage)
    except ValueError:
        raise HTTPException(403, "Invalid output path")

    if not resolved.is_file():
        raise HTTPException(404, "Output file missing")
    return FileResponse(str(resolved), media_type="video/mp4", filename=f"job_{job.id}_render.mp4")