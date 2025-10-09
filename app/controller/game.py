from typing import List
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from app.crud.game import create_game_category, game_category
from app.db.dependency import get_db
from app.schemas.game import GameCategory


router = APIRouter(prefix="/games", tags=["Games"])

@router.get("/category", response_model=List[GameCategory])
def get_game_category(db: Session = Depends(get_db)):
    categories = game_category(db)
    return categories

@router.post("/category")
def add_game_category(name: str = Form(...), db: Session = Depends(get_db)):
    new_type = create_game_category(db, name)
    return {"message": "เพิ่มประเภทเกมสำเร็จ", "data": new_type}