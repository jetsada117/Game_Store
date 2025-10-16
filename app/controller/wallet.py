from typing import Literal, Optional
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


from fastapi import APIRouter, Depends, Form, Query
from sqlalchemy.orm import Session
from app.db.dependency import get_db
from app.crud import wallet as crud_wallet
from fastapi import HTTPException
from sqlalchemy.sql import text

router = APIRouter(prefix="/wallet", tags=["Users"])


@router.post("/buy/{user_id}/{game_id}")
def buy_one(
    user_id: int,
    game_id: int,
    discount_code: str | None = Form(None), 
    db: Session = Depends(get_db),
):
    discount_code_id = None
    if discount_code:
        code = crud_wallet.get_discount_code_by_codeva(db, discount_code)

        if not code:
            raise HTTPException(status_code=404, detail="ไม่พบโค้ดส่วนลดนี้หรือโค้ดไม่พร้อมใช้งาน")
        
        discount_code_id = code["id"]

    result = crud_wallet.purchase_one_game(
        db=db,
        user_id=user_id,
        game_id=game_id,
        discount_code_id=discount_code_id
    )

    return {"message": "คุณซื้อเกมสำเร็จ!"}


@router.post("/buy/{user_id}")
def buy_many(
    user_id: int,
    game_ids: list[int] = Form(...), 
    discount_code: str | None = Form(None),
    db: Session = Depends(get_db),
):
    discount_code_id = None
    if discount_code:
        code = crud_wallet.get_discount_code_by_codeva(db, discount_code)

        if not code:
            raise HTTPException(status_code=404, detail="ไม่พบโค้ดส่วนลดนี้หรือโค้ดไม่พร้อมใช้งาน")
        
        discount_code_id = code["id"]

    result = crud_wallet.purchase_games(
        db=db,
        user_id=user_id,
        game_ids=game_ids,
        discount_code_id=discount_code_id
    )

    return {"message": "คุณซื้อเกมสำเร็จ!"}


@router.get("/transaction/{user_id}")
def my_transactions(user_id: int, db: Session = Depends(get_db)):
    return crud_wallet.get_user_transactions(db, user_id)


@router.post("/discount")
def create_discount_form(
    code: Optional[str] = Form(None),               
    type: str = Form("percent"),
    value: float = Form(...),
    max_discount: Optional[float] = Form(None),
    usage_limit: int = Form(...),
    status: str = Form("active"),
    db: Session = Depends(get_db)
):
    result = crud_wallet.create_discount_code(
        db=db,
        code=code,                     
        type_=type,
        value=value,
        max_discount=max_discount,
        usage_limit=usage_limit,
        status=status,
    )

    return result


@router.put("/discount/{code_id}")
def update_discount(
    code_id: int,
    type: Optional[Literal["percent", "fixed"]] = Form(None),
    value: Optional[float] = Form(None),
    max_discount: Optional[float] = Form(None),
    usage_limit: Optional[int] = Form(None),
    status: Optional[Literal["active", "inactive"]] = Form(None),
    code: Optional[str] = Form(None),  
    db: Session = Depends(get_db),
):
    result = crud_wallet.update_discount_code(
        db=db,
        code_id=code_id,
        type_=type,
        value=value,
        max_discount=max_discount,
        usage_limit=usage_limit,
        status=status,
        new_code=code,                   
    )
    return result


@router.get("/discount/all")
def read_all_discounts(db: Session = Depends(get_db)):
    return crud_wallet.get_all_discount_codes(db)


@router.get("/discount/allwithusage")
def read_all_discounts(db: Session = Depends(get_db)):
    return crud_wallet.get_all_discount_codes_with_usage(db)


@router.delete("/discount/{code_id}")
def delete_code(code_id: int, db: Session = Depends(get_db)):
    return crud_wallet.delete_discount_code(db, code_id)


@router.get("/discount/search/")
def read_discount_by_code(code: str, db: Session = Depends(get_db)):
    return crud_wallet.get_discount_code_by_codeva(db, code)


@router.get("/discount/{code_id}")
def read_discount_by_id(code_id: int, db: Session = Depends(get_db)):
    return crud_wallet.get_discount_code(db, code_id)

