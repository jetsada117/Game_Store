from sqlalchemy.orm import Session
from app.db import models
from app.schemas.user import UserCreate
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

def create_user(db: Session, user):
    sql = text("""
        INSERT INTO users (username, email, password_hash, img_url, role, wallet_balance, created_at, updated_at)
        VALUES (:username, :email, :password_hash, :img_url, :role, :wallet_balance, :created_at, :updated_at);
    """)
    db.execute(sql, {
        "username": user.username,
        "email": user.email,
        "password_hash": user.password_hash,
        "img_url": user.img_url,
        "role": "USER",
        "wallet_balance": 0.00,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })
    db.commit()

    result = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": user.email})
    db_user = result.fetchone()
    return db_user


def get_users(db: Session):
    query = text("SELECT * FROM users")
    result = db.execute(query)
    return result.fetchall()

