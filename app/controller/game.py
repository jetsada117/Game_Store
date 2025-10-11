from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.crud import game as crud_game
from app.db.dependency import get_db
from app.schemas.game import GameBase, GameCategory, GameResponse, GameUpdate

router = APIRouter(prefix="/games", tags=["Games"])

@router.get("/category", response_model=List[GameCategory])
def get_game_category(db: Session = Depends(get_db)):
    categories = crud_game.get_game_category(db)
    return categories

@router.post("/category", status_code=status.HTTP_201_CREATED)
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

@router.get("/", response_model=List[GameResponse])
def get_game_all(db: Session = Depends(get_db)):
    return crud_game.get_game_all(db)

@router.get("/{game_id}", response_model=GameResponse)
def get_game_byId(game_id: int, db: Session = Depends(get_db)):
    return crud_game.get_game(db, game_id)

@router.put("/{game_id}")
def update_game_info(
    game_id: int,
    name: str | None = Form(None),
    type_id: int | None = Form(None),
    description: str | None = Form(None),
    price: float | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    current = crud_game.get_game(db, game_id)
    if not current:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลเกมนี้")

    payload = GameUpdate(
        name=name if name is not None else current["name"],
        type_id=type_id if type_id is not None else current["type_id"],
        description=description if description is not None else current["description"],
        price=price if price is not None else current["price"],
    )

    try:
        if image:
            game = crud_game.update_game_with_file(db, game_id, payload, image)
        else:
            game = crud_game.update_game_without_file(db, game_id, payload)

        if not game:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลเกมนี้")

        return {"message": "Game updated successfully"}
    
    except HTTPException as e:
        if e.status_code == 409:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"message": "ชื่อเกมนี้ถูกใช้แล้ว"}
            )
        raise