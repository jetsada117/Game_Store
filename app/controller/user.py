from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.crud import user as crud_user
from app.db.dependency import get_db
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return crud_user.create_user(db, user)

@router.get("/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return crud_user.get_users(db)
