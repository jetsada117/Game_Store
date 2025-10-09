from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from app.crud.game import create_game_type
from app.db.dependency import get_db


router = APIRouter(prefix="/games", tags=["Games"])

@router.post("/type")
def add_game_type(name: str = Form(...), db: Session = Depends(get_db)):
    new_type = create_game_type(db, name)
    return {"message": "เพิ่มประเภทเกมสำเร็จ", "data": new_type}