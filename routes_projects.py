from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .db import get_db
from .models import Project
from .auth import current_user

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    brief: str = ""

@router.post("")
def create_project(body: ProjectCreate, user=Depends(current_user), db: Session=Depends(get_db)):
    p=Project(owner_id=user.id,name=body.name,brief=body.brief)
    db.add(p); db.commit(); db.refresh(p)
    return {"id":p.id,"name":p.name,"brief":p.brief}

@router.get("")
def list_projects(user=Depends(current_user), db: Session=Depends(get_db)):
    return [{"id":p.id,"name":p.name,"brief":p.brief} for p in db.query(Project).filter(Project.owner_id==user.id).all()]
