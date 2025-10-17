from typing import Dict, List, Literal
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


def delete_game_and_dependencies(db: Session, game_id: int):
    """
    ลบเกมและความสัมพันธ์ที่อ้างถึงเกมนี้ทั้งหมด
    - ลบ user_game_licenses ที่ game_id = :gid
    - ลบ order_items ที่ game_id = :gid
    - อัปเดต orders ที่ได้รับผลกระทบ (recalc subtotal/total)
    - ลบเกมจาก games
    *หมายเหตุ*: ไม่ลบ orders/transactions เพื่อคงประวัติการชำระเงิน
    """
    try:
        game = db.execute(
            text("SELECT id, name FROM games WHERE id = :gid"),
            {"gid": game_id}
        ).mappings().first()
        if not game:
            raise HTTPException(status_code=404, detail="ไม่พบเกมที่ต้องการลบ")

        affected_order_ids: List[int] = db.execute(
            text("""
                SELECT DISTINCT order_id
                FROM order_items
                WHERE game_id = :gid
            """),
            {"gid": game_id}
        ).scalars().all()

        del_licenses = db.execute(
            text("DELETE FROM user_game_licenses WHERE game_id = :gid"),
            {"gid": game_id}
        ).rowcount

        del_order_items = db.execute(
            text("DELETE FROM order_items WHERE game_id = :gid"),
            {"gid": game_id}
        ).rowcount

        updated_orders = 0
        if affected_order_ids:
            recalc_rows = db.execute(
                text("""
                    SELECT
                        o.id,
                        COALESCE(SUM(oi.unit_price * oi.quantity), 0) AS new_subtotal,
                        o.discount_amount
                    FROM orders o
                    LEFT JOIN order_items oi ON oi.order_id = o.id
                    WHERE o.id IN :oids
                    GROUP BY o.id, o.discount_amount
                """),
                {"oids": tuple(affected_order_ids)}
            ).mappings().all()

            for r in recalc_rows:
                new_subtotal = float(r["new_subtotal"] or 0)
                discount     = float(r["discount_amount"] or 0)
                new_total    = max(0.0, new_subtotal - discount)

                db.execute(
                    text("""
                        UPDATE orders
                           SET subtotal_amount = :subt,
                               total_amount    = :tot
                         WHERE id = :oid
                    """),
                    {"subt": new_subtotal, "tot": new_total, "oid": int(r["id"])}
                )
                updated_orders += 1

        db.execute(text("DELETE FROM games WHERE id = :gid"), {"gid": game_id})

        db.commit()

        return {"message": f"ลบเกม '{game['name']}' (id={game_id}) สำเร็จ"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"ลบเกมไม่สำเร็จ: {e}")
    

def get_purchased_games_by_user(db: Session, user_id: int):
    sql = text("""
        SELECT 
            g.id AS id,
            g.name AS name,
            gc.name AS category_name,
            g.description,
            g.price,
            g.release_date,
            g.image_url
        FROM user_game_licenses ugl
        JOIN games g ON ugl.game_id = g.id
        LEFT JOIN game_category gc ON g.category_id = gc.id
        WHERE ugl.user_id = :uid
    """)

    result = db.execute(sql, {"uid": user_id}).mappings().all()
    return result


def get_daily_top_selling_games(
    db: Session,
    days: int = 7,
    top_n: int = 5,
    order_by: Literal["units", "revenue"] = "units",
):
    order_col = "total_units" if order_by == "units" else "total_revenue"

    sql = text(f"""
        WITH daily AS (
            SELECT
                DATE(o.created_at)               AS sale_date,
                g.id                             AS game_id,
                g.name                           AS game_name,
                gc.name                          AS category_name,
                g.image_url                      AS image_url,   
                SUM(oi.quantity)                 AS total_units,
                SUM(oi.quantity * oi.unit_price) AS total_revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            JOIN games g        ON g.id = oi.game_id
            LEFT JOIN game_category gc ON gc.id = g.category_id
            WHERE o.status = 'fulfilled'
              AND o.created_at >= DATE_SUB(CURDATE(), INTERVAL :days_minus_one DAY)
              AND o.created_at <  DATE_ADD(CURDATE(), INTERVAL 1 DAY)
            GROUP BY DATE(o.created_at), g.id, g.name, gc.name, g.image_url 
        ),
        ranked AS (
            SELECT
                d.*,
                ROW_NUMBER() OVER (
                    PARTITION BY d.sale_date
                    ORDER BY d.{order_col} DESC, d.total_revenue DESC, d.game_name ASC
                ) AS rnk
            FROM daily d
        )
        SELECT
            sale_date,
            game_id,
            game_name,
            category_name,
            image_url,      
            total_units,
            total_revenue,
            rnk
        FROM ranked
        WHERE rnk <= :top_n
        ORDER BY sale_date DESC, rnk ASC;
    """)

    rows = db.execute(sql, {
        "days_minus_one": max(0, days - 1),
        "top_n": top_n
    }).mappings().all()

    def format_thai_date(dt: datetime.date) -> str:
        if not dt:
            return "-"
        return f"{dt.day:02d}/{dt.month:02d}/{dt.year + 543}"

    grouped: Dict[str, List[Dict]] = {}
    for r in rows:
        sale_date_th = format_thai_date(r["sale_date"])
        grouped.setdefault(sale_date_th, []).append({
            "rank": r["rnk"],
            "game_id": r["game_id"],
            "game_name": r["game_name"],
            "category_name": r["category_name"],
            "image_url": r["image_url"],
            "total_units": int(r["total_units"] or 0),
            "total_revenue": float(r["total_revenue"] or 0.0),
        })

    return [{"date": d, "top": grouped[d]} for d in sorted(grouped.keys(), reverse=True)]

