from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from app.db.dependency import get_db
from app.services.auth_service import login_plain

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    return login_plain(db, email, password)
