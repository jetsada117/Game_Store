from fastapi import HTTPException
from pymysql import IntegrityError
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
from app.services.upload_service import upload_avatar
from app.core.security import hash_password, verify_password


def _email_exists(db: Session, email: str, exclude_user_id: int | None = None) -> bool:
    if exclude_user_id is None:
        sql = text("SELECT 1 FROM users WHERE email = :email LIMIT 1")
        return db.execute(sql, {"email": email}).scalar() is not None
    else:
        sql = text("SELECT 1 FROM users WHERE email = :email AND id <> :id LIMIT 1")
        return db.execute(sql, {"email": email, "id": exclude_user_id}).scalar() is not None
    

def create_user_with_file(db: Session, user, image_file) -> dict | None:
    if _email_exists(db, user.email):
        raise HTTPException(status_code=409, detail="อีเมลนี้ถูกใช้แล้ว")

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
        text("SELECT id, username, email, img_url, role FROM users WHERE email = :email"),
        {"email": user.email}
    ).mappings().first()
    return row


def get_users(db: Session):
    result = db.execute(text("SELECT * FROM users"))
    return result.fetchall()


def get_user_by_email(db: Session, email: str):
    row = db.execute(
        text("SELECT id, username, password_hash, email, img_url, role, wallet_balance FROM users WHERE email = :email"),
        {"email": email}
    ).mappings().first()
    return row


def _update_user_simple(db: Session, user_id: int, data: dict) -> dict | None:
    if not data:
        return None
    data["updated_at"] = datetime.now()
    set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
    sql = text(f"UPDATE users SET {set_clause} WHERE id = :id")
    data["id"] = user_id
    try:
        db.execute(sql, data)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="อีเมลนี้ถูกใช้แล้ว")
    row = db.execute(text("SELECT id, username, email, img_url, role, wallet_balance FROM users WHERE id = :id"), {"id": user_id}).mappings().first()
    return row


def update_profile(db: Session, user_id: int, payload) -> dict | None:
    data_in = payload.dict(exclude_unset=True) if hasattr(payload, "dict") else dict(payload or {})
    updated: dict = {}

    if "username" in data_in and data_in["username"] is not None:
        updated["username"] = data_in["username"]

    if "email" in data_in and data_in["email"]:
        if _email_exists(db, data_in["email"], exclude_user_id=user_id):
            raise HTTPException(status_code=409, detail="อีเมลนี้ถูกใช้แล้ว")
        updated["email"] = data_in["email"]

    return _update_user_simple(db, user_id, updated)


def update_profile_with_file(db: Session, user_id: int, payload, image_file) -> dict | None:
    data_in = payload.dict(exclude_unset=True) if hasattr(payload, "dict") else dict(payload or {})
    updated: dict = {}

    if "username" in data_in and data_in["username"] is not None:
        updated["username"] = data_in["username"]

    if "email" in data_in and data_in["email"]:
        if _email_exists(db, data_in["email"], exclude_user_id=user_id):
            raise HTTPException(status_code=409, detail="อีเมลนี้ถูกใช้แล้ว")
        updated["email"] = data_in["email"]

    if image_file:
        file_bytes = image_file.file.read()
        img_url = upload_avatar(
            file_bytes=file_bytes,
            filename=image_file.filename,
            content_type=image_file.content_type or "application/octet-stream"
        )
        updated["img_url"] = img_url

    return _update_user_simple(db, user_id, updated)


def update_password(db: Session, user_id: int, current_password: str, new_password: str) -> dict | None:
    row = db.execute(text("SELECT id, password_hash FROM users WHERE id = :id"),
                     {"id": user_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="รหัสผ่านเดิมไม่ถูกต้อง")

    new_hash = hash_password(new_password)
    return _update_user_simple(db, user_id, {"password_hash": new_hash})

