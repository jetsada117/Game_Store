from sqlalchemy import text
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.upload_service import upload_game_image

def create_game_with_file(db: Session, game, image_file) -> dict | None:
    existing = db.execute(
        text("SELECT id FROM games WHERE name = :name"),
        {"name": game.name}
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="ชื่อเกมนี้ถูกใช้แล้ว")

    file_bytes = image_file.file.read()
    img_url = upload_game_image(
        file_bytes=file_bytes,
        filename=image_file.filename,
        content_type=image_file.content_type or "application/octet-stream"
    )

    sql = text("""
        INSERT INTO games (name, type_id, description, price, release_date, image_url, created_at)
        VALUES (:name, :type_id, :description, :price, :release_date, :image_url, :created_at);
    """)

    params = {
        "name": game.name,
        "type_id": game.type_id,
        "description": game.description,
        "price": game.price,
        "release_date": game.release_date,
        "image_url": img_url,
        "created_at": datetime.now()
    }

    db.execute(sql, params)
    db.commit()

    row = db.execute(
        text("SELECT id, name, type_id, description, price, release_date, image_url, created_at FROM games WHERE name = :name"),
        {"name": game.name}
    ).mappings().first()

    return row


def create_game_category(db: Session, name: str) -> dict | None:
    existing = db.execute(
        text("SELECT id FROM game_category WHERE name = :name"),
        {"name": name}
    ).first()

    
    if existing:
        raise HTTPException(status_code=409, detail="ชื่อประเภทเกมนี้มีอยู่แล้ว")


    sql = text("""
        INSERT INTO game_category (name)
        VALUES (:name);
    """)
    db.execute(sql, {"name": name})
    db.commit()


    row = db.execute(
        text("SELECT id, name FROM game_category WHERE name = :name"),
        {"name": name}
    ).mappings().first()

    return row


def get_game_category(db: Session):
    try:
        result = db.execute(text("SELECT * FROM game_category ORDER by id")).mappings().all() 

        if not result:
            raise HTTPException(status_code=404, detail="No game categories found")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")