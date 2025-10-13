from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.crud.user import get_user_by_email
from app.core.security import verify_password

def login_plain(db: Session, email: str, password: str) -> dict:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=401, message="Invalid email or password")
    
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, message="Invalid email or password")

    return user