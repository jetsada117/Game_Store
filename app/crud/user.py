from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
from app.services.upload_service import upload_avatar
from app.core.security import hash_password


def create_user_with_file(db: Session, user, image_file) -> dict | None:
    file_bytes = image_file.file.read()
    img_url = upload_avatar(
        file_bytes=file_bytes,
        filename=image_file.filename,
        content_type=image_file.content_type or "application/octet-stream"
    )

    password_hashed = hash_password(user.password)

    sql = text("""
        INSERT INTO users (username, email, password_hash, img_url, role, wallet_balance, created_at, updated_at)
        VALUES (:username, :email, :password_hash, :img_url, :role, :wallet_balance, :created_at, :updated_at);
    """)
    params = {
        "username": user.username,
        "email": user.email,
        "password_hash": password_hashed,
        "img_url": img_url,
        "role": "USER",
        "wallet_balance": 0.00,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    db.execute(sql, params)
    db.commit()

    row = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": user.email}
    ).mappings().first()
    return dict(row) if row else None


def get_users(db: Session):
    result = db.execute(text("SELECT * FROM users"))
    return result.fetchall()


def get_user_by_email(db: Session, email: str):
    row = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    ).mappings().first()
    return row
