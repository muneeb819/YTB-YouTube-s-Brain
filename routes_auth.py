from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .auth import verify_password, create_token, current_user

router = APIRouter()

class Login(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(body: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_token(user.id), "token_type": "bearer"}

@router.get("/me")
def me(user=Depends(current_user)):
    return {"id": user.id, "email": user.email, "is_admin": user.is_admin}
