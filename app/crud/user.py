from sqlalchemy.orm import Session
from app.db import models
from app.schemas.user import UserCreate
from sqlalchemy import text

def create_user(db: Session, user: UserCreate):
    sql = text("""
        INSERT INTO users (username, email)
        VALUES (:username, :email)
        RETURNING *
    """)
    result = db.execute(sql, {"username": user.username, "email": user.email})
    db.commit()
    db_user = result.fetchone()
    return db_user

def get_users(db: Session):
    query = text("SELECT * FROM users")
    result = db.execute(query)
    return result.fetchall()

