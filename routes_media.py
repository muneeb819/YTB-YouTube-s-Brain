import json, shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from .models import Project, MediaAsset
from .auth import current_user
from .config import settings
from .media import probe

router=APIRouter()

@router.post("/upload/{project_id}")
def upload(project_id:int, file:UploadFile=File(...), user=Depends(current_user), db:Session=Depends(get_db)):
    project=db.query(Project).filter(Project.id==project_id,Project.owner_id==user.id).first()
    if not project: raise HTTPException(404,"Project not found")
    folder=Path(settings.ytb_storage_dir)/str(user.id)/str(project_id)
    folder.mkdir(parents=True,exist_ok=True)
    safe=Path(file.filename or "upload.bin").name
    path=folder/safe
    with path.open("wb") as f: shutil.copyfileobj(file.file,f)
    try: info=probe(str(path))
    except Exception as e: info={"probe_error":str(e)}
    asset=MediaAsset(project_id=project_id,filename=safe,path=str(path),
                     mime_type=file.content_type or "application/octet-stream",
                     probe_json=json.dumps(info))
    db.add(asset);db.commit();db.refresh(asset)
    return {"id":asset.id,"filename":asset.filename,"probe":info}
