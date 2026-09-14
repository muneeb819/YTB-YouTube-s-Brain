from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .auth import current_user
from .ai import provider

router=APIRouter()

class Prompt(BaseModel):
    prompt:str

@router.post("/generate")
def generate(body:Prompt,user=Depends(current_user)):
    try:
        text=provider().generate(body.prompt)
        return {"text":text}
    except Exception as e:
        raise HTTPException(502,detail=str(e))
