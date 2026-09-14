import json
import shutil
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import current_user
from .config import settings
from .db import get_db
from .media import probe
from .models import MediaAsset, Project

router = APIRouter()


class RightsUpdate(BaseModel):
    status: Literal["COMPLIANT", "BLOCKED", "UNKNOWN"]


@router.post("/upload/{project_id}")
def upload(project_id: int, file: UploadFile = File(...), user=Depends(current_user), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    folder = Path(settings.ytb_storage_dir) / str(user.id) / str(project_id)
    folder.mkdir(parents=True, exist_ok=True)

    original = Path(file.filename or "upload.bin").name
    safe = f"{uuid.uuid4().hex[:12]}_{original}"
    path = folder / safe

    written = 0
    try:
        with path.open("wb") as f:
            while chunk := file.file.read(1024 * 1024):
                written += len(chunk)
                if written > settings.max_upload_bytes:
                    raise HTTPException(413, "Upload exceeds the configured size limit")
                f.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise

    try:
        info = probe(str(path))
    except Exception as e:
        info = {"probe_error": str(e)}

    asset = MediaAsset(
        project_id=project_id,
        filename=safe,
        path=str(path),
        mime_type=file.content_type or "application/octet-stream",
        probe_json=json.dumps(info),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"id": asset.id, "filename": asset.filename, "probe": info}


@router.post("/{asset_id}/rights")
def set_rights(asset_id: int, body: RightsUpdate, user=Depends(current_user), db: Session = Depends(get_db)):
    asset = db.get(MediaAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    project = db.get(Project, asset.project_id)
    if not project or (project.owner_id != user.id and not user.is_admin):
        raise HTTPException(403, "Forbidden")
    asset.rights_status = body.status
    db.commit()
    return {"asset_id": asset.id, "rights_status": asset.rights_status}


@router.get("/{asset_id}/download")
def download(asset_id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    asset = db.get(MediaAsset, asset_id)
    if not asset:
        raise HTTPException(404, "Asset not found")
    project = db.get(Project, asset.project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(403, "Forbidden")

    path = Path(asset.path)
    storage = Path(settings.ytb_storage_dir).resolve()
    try:
        resolved = path.resolve()
        resolved.relative_to(storage)
    except ValueError:
        raise HTTPException(403, "Invalid asset path")

    if not resolved.is_file():
        raise HTTPException(404, "Asset file missing")
    return FileResponse(str(resolved), filename=asset.filename)