import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .db import get_db
from .models import Project, MediaAsset, Job
from .auth import current_user
from .jobs import submit_render

router=APIRouter()

class RenderRequest(BaseModel):
    project_id:int
    asset_id:int
    start:float=0
    duration:float|None=None

@router.post("/render")
def render(body:RenderRequest,user=Depends(current_user),db:Session=Depends(get_db)):
    p=db.query(Project).filter(Project.id==body.project_id,Project.owner_id==user.id).first()
    a=db.query(MediaAsset).filter(MediaAsset.id==body.asset_id,MediaAsset.project_id==body.project_id).first()
    if not p or not a: raise HTTPException(404,"Project or asset not found")
    j=Job(project_id=p.id,type="FFMPEG_RENDER",state="QUEUED",
          input_json=json.dumps(body.model_dump()))
    db.add(j);db.commit();db.refresh(j)
    submit_render(j.id,a.id,body.start,body.duration)
    return {"job_id":j.id,"state":j.state}

@router.get("/{job_id}")
def get_job(job_id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    j=db.get(Job,job_id)
    if not j: raise HTTPException(404,"Job not found")
    p=db.get(Project,j.project_id)
    if not p or p.owner_id!=user.id: raise HTTPException(403,"Forbidden")
    return {"id":j.id,"type":j.type,"state":j.state,"output":json.loads(j.output_json or "{}"),"error":j.error}
