from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.crud import game as crud_game
from app.db.dependency import get_db
from app.schemas.game import GameBase, GameCategory


router = APIRouter(prefix="/games", tags=["Games"])

@router.get("/category", response_model=List[GameCategory])
def get_game_category(db: Session = Depends(get_db)):
    categories = crud_game.get_game_category(db)
    return categories

@router.post("/category", status_code= status.HTTP_201_CREATED)
def add_game_category(name: str = Form(...), db: Session = Depends(get_db)):
    new_type = crud_game.create_game_category(db, name)
    return {"message": "เพิ่มประเภทเกมสำเร็จ", "data": new_type}

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user_with_image(
    name: str = Form(...),
    type_id: int = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    image:  UploadFile = File(...),          
    db: Session = Depends(get_db)
):
    if image.content_type not in {"image/png", "image/jpeg"}:
        raise HTTPException(status_code=400, detail="Only PNG/JPEG are allowed")

    game = GameBase(
        name = name,
        type_id = type_id,
        description = description,
        price = price,
        image_url = ""
    )

    created = crud_game.create_game_with_file(db, game, image) 
    if not created:
        raise HTTPException(status_code=400, detail="Create user failed")
    return {"message": "Create updated successfully"}