from sqlalchemy.orm import Session
from app.db import models
from app.schemas.user import UserCreate
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
from app.services.upload_service import upload_avatar

def create_user_with_file(db: Session, user, image_file) -> dict | None:
    # 1) อัปโหลดรูปขึ้น Supabase
    file_bytes = image_file.file.read()
    img_url = upload_avatar(
        file_bytes=file_bytes,
        filename=image_file.filename,
        content_type=image_file.content_type or "application/octet-stream"
    )

    # 2) บันทึกลง MySQL (เก็บ URL ที่ได้)
    sql = text("""
        INSERT INTO users (username, email, password_hash, img_url, role, wallet_balance, created_at, updated_at)
        VALUES (:username, :email, :password_hash, :img_url, :role, :wallet_balance, :created_at, :updated_at);
    """)
    params = {
        "username": user.username,
        "email": user.email,
        "password_hash": user.password_hash,  # หรือ hash ก่อนถ้า user.password
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
    query = text("SELECT * FROM users")
    result = db.execute(query)
    return result.fetchall()

