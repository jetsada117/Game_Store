from sqlalchemy import text
from datetime import datetime
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.services.upload_service import upload_game_image
from app.utils.function import thai_date

def get_game_all(db: Session) -> dict | None:
    sql = text("""
        SELECT 
            g.id, g.name, c.name AS category_name,
            g.description, g.price, g.release_date, g.image_url
        FROM games AS g
        JOIN game_category AS c ON g.category_id = c.id
        ORDER BY g.id
    """)

    rows = db.execute(sql).mappings().all()
    return rows


def get_game_by_name(db: Session, keyword: str) -> list[dict] | None:
    sql = text("""
        SELECT 
            g.id, g.name, c.name AS category_name,
            g.description, g.price, g.release_date, g.image_url
        FROM games AS g
        JOIN game_category AS c ON g.category_id = c.id
        WHERE g.name LIKE :keyword
        ORDER BY g.id
    """)

    rows = db.execute(sql, {"keyword": f"%{keyword.lower()}%"}).mappings().all()
    return rows


def get_game(db: Session, game_id: int) -> dict | None:
    result = db.execute(
        text("""
            SELECT
                g.id,
                g.name,
                c.name AS category_name,
                g.description,
                g.price,
                g.release_date,
                g.image_url
            FROM games AS g
            JOIN game_category AS c ON g.category_id = c.id
            WHERE g.id = :id
        """),
        {"id": game_id}
    ).mappings().first()

    if not result:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลเกมนี้")

    return result


def unique_name(db: Session, name: str, game_id: int) -> None:
    dup = db.execute(
        text("SELECT id FROM games WHERE name = :name AND id <> :id"),
        {"name": name, "id": game_id}
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail="ชื่อเกมนี้ถูกใช้แล้ว")

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
        INSERT INTO games (name, category_id, description, price, release_date, image_url, created_at)
        VALUES (:name, :category_id, :description, :price, :release_date, :image_url, :created_at);
    """)

    params = {
        "name": game.name,
        "category_id": game.category_id,
        "description": game.description,
        "price": game.price,
        "release_date": thai_date(),
        "image_url": img_url,
        "created_at": datetime.now()
    }

    db.execute(sql, params)
    db.commit()

    row = db.execute(
        text("SELECT id, name, category_id, description, price, release_date, image_url, created_at FROM games WHERE name = :name"),
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
    

def update_game_without_file(db: Session, game_id: int, game) -> dict:
    existing = get_game(db, game_id)
    if not existing:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลเกมนี้")

    unique_name(db, game.name, game_id)

    sql = text("""
        UPDATE games
        SET name = :name,
            category_id = :category_id,
            description = :description,
            price = :price
        WHERE id = :id
    """)

    params = {
        "id": game_id,
        "name": game.name,
        "category_id": game.category_id,
        "description": game.description,
        "price": game.price,
    }

    db.execute(sql, params)
    db.commit()

    result = get_game(db, game_id)
    return result

def update_game_with_file(db: Session, game_id: int, game, image_file: UploadFile) -> dict:
    existing = get_game(db, game_id)
    if not existing:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลเกมนี้")

    unique_name(db, game.name, game_id)

    if image_file.content_type not in {"image/png", "image/jpeg"}:
        raise HTTPException(status_code=400, detail="อนุญาตเฉพาะภาพ PNG/JPEG")

    file_bytes = image_file.file.read()
    img_url = upload_game_image(
        file_bytes=file_bytes,
        filename=image_file.filename,
        content_type=image_file.content_type or "application/octet-stream",
    )

    sql = text("""
        UPDATE games
        SET name = :name,
            category_id = :category_id,
            description = :description,
            price = :price,
            image_url = :image_url
        WHERE id = :id
    """)

    params = {
        "id": game_id,
        "name": game.name,
        "category_id": game.category_id,
        "description": game.description,
        "price": game.price,
        "image_url": img_url,
    }

    db.execute(sql, params)
    db.commit()

    result = get_game(db, game_id)
    return result