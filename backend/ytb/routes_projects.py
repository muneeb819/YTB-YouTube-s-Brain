import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import current_user
from .db import get_db
from .models import Job, MediaAsset, Project
from .safety import preflight

router = APIRouter()

_RANK = {"PASS": 0, "REVIEW": 1, "REPAIR": 2, "BLOCK": 3}


class ProjectCreate(BaseModel):
    name: str
    brief: str = ""


@router.post("")
def create_project(body: ProjectCreate, user=Depends(current_user), db: Session = Depends(get_db)):
    project = Project(owner_id=user.id, name=body.name, brief=body.brief)
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name, "brief": project.brief}


@router.get("")
def list_projects(user=Depends(current_user), db: Session = Depends(get_db)):
    return [
        {"id": p.id, "name": p.name, "brief": p.brief}
        for p in db.query(Project).filter(Project.owner_id == user.id).all()
    ]


@router.get("/{project_id}/assets")
def list_assets(project_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    assets = db.query(MediaAsset).filter(MediaAsset.project_id == project_id).all()
    return [
        {
            "id": a.id,
            "filename": a.filename,
            "mime_type": a.mime_type,
            "rights_status": a.rights_status,
            "probe": json.loads(a.probe_json or "{}"),
        }
        for a in assets
    ]


@router.get("/{project_id}/jobs")
def list_jobs(project_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    jobs = (
        db.query(Job)
        .filter(Job.project_id == project_id)
        .order_by(Job.created_at.desc())
        .all()
    )
    return [
        {
            "id": j.id,
            "type": j.type,
            "state": j.state,
            "error": j.error,
            "output": json.loads(j.output_json or "{}"),
        }
        for j in jobs
    ]


@router.get("/{project_id}/preflight")
def project_preflight(project_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    assets = db.query(MediaAsset).filter(MediaAsset.project_id == project_id).all()
    verdicts = []
    worst = "PASS"
    for asset in assets:
        verdict = preflight(asset.rights_status)
        if _RANK[verdict] > _RANK[worst]:
            worst = verdict
        verdicts.append(
            {
                "asset_id": asset.id,
                "filename": asset.filename,
                "rights_status": asset.rights_status,
                "verdict": verdict,
            }
        )
    return {"project_id": project_id, "verdict": worst, "assets": verdicts}