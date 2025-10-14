from typing import Optional
from fastapi import APIRouter, Depends, Form, Path
from sqlalchemy.orm import Session
from app.db.dependency import get_db
from app.schemas.user import MoneyUpdate
from app.crud import wallet as crud_wallet

router = APIRouter(prefix="/wallet", tags=["Users"])

@router.get("/{user_id}")
def get_balance(
    user_id: int =  Path(..., get=0),
    db: Session = Depends(get_db)
):
    return crud_wallet.get_balance(db, user_id)

@router.post("/topup/{user_id}", response_model=MoneyUpdate)
def add_balance(
    user_id: int = Path(..., gt=0),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    result = crud_wallet.add_balance(db, user_id, amount)
    return result

@router.post("/buy/{user_id}/{game_id}")
def buy_one(user_id: int, game_id: int, db: Session = Depends(get_db)):
    result = crud_wallet.purchase_one_game(db, user_id, game_id)
    return {"message": "คุณซื้อเกมสำเร็จ!"}

@router.post("/buy/{user_id}")
def buy_many(user_id: int, game_ids: list[int], db: Session = Depends(get_db)):
    result = crud_wallet.purchase_games(db, user_id, game_ids)
    return {"message": "คุณซื้อเกมสำเร็จ!"}


@router.get("/transaction/{user_id}")
def my_transactions(user_id: int, db: Session = Depends(get_db)):
    return crud_wallet.get_user_transactions(db, user_id)

from fastapi import Form

@router.post("/discount")
def create_discount_form(
    type: str = Form("percent"),
    value: float = Form(...),
    max_discount: float = Form(...),
    start_at: str = Form(...),
    end_at: str = Form(...),
    usage_limit: int = Form(...),
    status: str = Form("active"),
    db: Session = Depends(get_db)
):
    result = crud_wallet.create_discount_code(
        db,
        type_ = type,
        value = value,
        max_discount = max_discount,
        start_at = start_at,
        end_at = end_at,
        usage_limit = usage_limit,
        status = status
    )

    return result
