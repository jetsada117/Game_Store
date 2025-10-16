from datetime import datetime, timedelta, timezone
import re
from typing import Iterable, Literal, Optional
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.utils import function 

def get_balance(db: Session, user_id: int):
    result = db.execute(
        text("SELECT id, wallet_balance FROM users WHERE id = :id"),
        {"id": user_id}
    ).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="ไม่พบบัญชีผู้ใช้")
    
    return result

def add_balance(db: Session, user_id: int, amount: float):
    user = db.execute(
        text("SELECT id, wallet_balance FROM users WHERE id = :id"),
        {"id": user_id}
    ).mappings().first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบบัญชีผู้ใช้")

    if amount is None or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")

    new_balance = float(user["wallet_balance"] or 0) + float(amount)

    db.execute(
        text("""
            UPDATE users
            SET wallet_balance = :balance
            WHERE id = :id
        """),
        {"id": user_id, "balance": new_balance}
    )

    db.execute(
    text("""
        INSERT INTO transactions (user_id, type, amount, status, processed_at)
        VALUES (:user_id, :type, :amount, :status, :processed_at)
    """),
        {
            "user_id": user_id,
            "type": "topup",
            "amount": float(amount),
            "status": "success",
            "processed_at": function.thai_date()
        }
    )

    db.commit()

    row = db.execute(
        text("SELECT id, wallet_balance FROM users WHERE id = :id"),
        {"id": user_id}
    ).mappings().first()

    return {"id": row.id,
            "amount": amount,
            "wallet_balance": row.wallet_balance
            }


def get_transactions_by_user_id(db: Session, user_id: int):
    sql = text("""
        SELECT id, user_id, type, order_id, amount, status, processed_at
        FROM transactions
        WHERE user_id = :uid
        ORDER BY id DESC
    """)

    params = {"uid": user_id}

    row = db.execute(sql, params).mappings().all()
    return row


def _load_discount(db, code_id: int):
    dc = db.execute(
        text("""
            SELECT id, code, type, value, max_discount, usage_limit, status
            FROM discount_codes
            WHERE id = :cid
        """),
        {"cid": code_id},
    ).mappings().first()
    if not dc:
        raise HTTPException(status_code=404, detail="ไม่พบโค้ดส่วนลดนี้")
    if dc["status"] != "active":
        raise HTTPException(status_code=400, detail="โค้ดนี้ไม่พร้อมใช้งาน")

    used = db.execute(
        text("SELECT COUNT(*) FROM discount_redemptions WHERE code_id = :cid"),
        {"cid": code_id},
    ).scalar() or 0

    if dc["usage_limit"] is not None and used >= int(dc["usage_limit"]):
        raise HTTPException(status_code=400, detail="โค้ดนี้ถูกใช้ครบจำนวนแล้ว")

    return dc


def _calc_discount(subtotal: float, dc: dict) -> float:
    t = dc["type"]
    val = float(dc["value"])
    if t == "percent":
        disc = subtotal * (val / 100.0)
        if dc["max_discount"] is not None:
            disc = min(disc, float(dc["max_discount"]))
    else:
        disc = min(val, subtotal)
    return max(0.0, round(disc, 2))


def purchase_games(
    db: Session,
    user_id: int,
    game_ids: Iterable[int],
    discount_code_id: Optional[int] = None, 
):
    game_ids = [int(g) for g in game_ids if g is not None]
    if not game_ids:
        raise HTTPException(status_code=400, detail="ต้องระบุ game_ids อย่างน้อย 1 รายการ")
    game_ids = sorted(set(game_ids))

    now_th = function.thai_date()
    try:

        user = db.execute(
            text("SELECT id, wallet_balance FROM users WHERE id = :uid FOR UPDATE"),
            {"uid": user_id}
        ).mappings().first()
        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบบัญชีผู้ใช้")

        wallet_balance = float(user["wallet_balance"] or 0)

        games = db.execute(
            text(f"""
                SELECT id, price, name
                FROM games
                WHERE id IN ({",".join([":g"+str(i) for i,_ in enumerate(game_ids)])})
            """),
            {("g"+str(i)): gid for i, gid in enumerate(game_ids)}
        ).mappings().all()

        if len(games) != len(game_ids):
            have_ids = {g["id"] for g in games}
            missing = [gid for gid in game_ids if gid not in have_ids]
            raise HTTPException(status_code=404, detail=f"ไม่พบเกม: {missing}")

        owned = db.execute(
            text(f"""
                SELECT game_id
                FROM user_game_licenses
                WHERE user_id = :uid
                  AND game_id IN ({",".join([":gg"+str(i) for i,_ in enumerate(game_ids)])})
            """),
            {"uid": user_id, **{("gg"+str(i)): gid for i, gid in enumerate(game_ids)}}
        ).scalars().all()
        if owned:
            raise HTTPException(status_code=400, detail=f"คุณมีเกมเหล่านี้อยู่แล้ว: {sorted(set(owned))}")

        subtotal = sum(float(g["price"]) for g in games)

        discount = 0.0
        discount_dc = None
        if discount_code_id is not None:
            discount_dc = _load_discount(db, discount_code_id)
            discount = _calc_discount(subtotal, discount_dc)

        total = max(0.0, round(subtotal - discount, 2))
        if wallet_balance < total:
            raise HTTPException(status_code=400, detail="ยอดเงินในวอลเล็ตไม่เพียงพอ")

        order_id = db.execute(
            text("""
                INSERT INTO orders
                    (user_id, subtotal_amount, discount_amount, total_amount, status, release_date)
                VALUES
                    (:uid, :subtotal, :discount, :total, 'pending', :release_date)
            """),
            {"uid": user_id, "subtotal": subtotal, "discount": discount, "total": total, "release_date": now_th}
        ).lastrowid

        db.execute(
            text("""
                INSERT INTO order_items (order_id, game_id, unit_price, quantity)
                VALUES (:oid, :gid, :price, 1)
            """),
            [
                {"oid": order_id, "gid": int(g["id"]), "price": float(g["price"])}
                for g in games
            ]
        )

        new_balance = wallet_balance - total
        db.execute(
            text("UPDATE users SET wallet_balance = :bal WHERE id = :uid"),
            {"bal": new_balance, "uid": user_id}
        )

        db.execute(
            text("""
                INSERT INTO transactions (user_id, order_id, type, amount, status, processed_at)
                VALUES (:uid, :oid, 'purchase', :amt, 'SUCCESS', :processed_at)
            """),
            {"uid": user_id, "oid": order_id, "amt": total, "processed_at": now_th}
        )

        db.execute(
            text("""
                INSERT INTO user_game_licenses (user_id, game_id, order_id)
                VALUES (:uid, :gid, :oid)
            """),
            [{"uid": user_id, "gid": int(g["id"]), "oid": order_id} for g in games]
        )

        if discount_dc is not None and discount > 0:
            db.execute(
                text("""
                    INSERT INTO discount_redemptions (code_id, user_id, order_id, discount_amount)
                    VALUES (:cid, :uid, :oid, :disc)
                """),
                {"cid": int(discount_dc["id"]), "uid": user_id, "oid": order_id, "disc": discount}
            )

        db.execute(
            text("UPDATE orders SET status='fulfilled', release_date=:now WHERE id=:oid"),
            {"now": now_th, "oid": order_id}
        )

        db.commit()

        return {
            "order_id": order_id,
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "games": [{"game_id": int(g["id"]), "name": g["name"]} for g in games],
            "used_code_id": int(discount_dc["id"]) if discount_dc else None,
            "order_time": now_th,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดระหว่างทำรายการ: {e}")


def purchase_one_game(
    db: Session,
    user_id: int,
    game_id: int,
    discount_code_id: Optional[int] = None
):
    return purchase_games(db, user_id, [game_id], discount_code_id=discount_code_id)


def get_user_transactions(db: Session, user_id: int):
    rows = db.execute(
        text("""
            SELECT id, user_id, type, order_id, amount, status, processed_at
            FROM transactions
            WHERE user_id = :uid
            ORDER BY processed_at DESC
        """),
        {"uid": user_id}
    ).mappings().all()
    return rows

# ---------- CREATE CODE ----------
def create_discount_code(
    db: Session,
    usage_limit: int,
    code: Optional[str] = None,  
    type_: Literal["percent", "fixed"] = "percent",
    value: float = 0,
    max_discount: Optional[float] = None,
    status: Literal["active", "inactive"] = "active",
):
    if not code or code.strip() == "":
        code = function._gen_code(6).upper().strip()
    else:
        code = code.upper().strip()

    if type_ not in ("percent", "fixed"):
        raise HTTPException(status_code=400, detail="type ต้องเป็น 'percent' หรือ 'fixed'")

    try:
        value = float(value)
    except Exception:
        raise HTTPException(status_code=400, detail="value ต้องเป็นตัวเลข")

    if type_ == "percent":
        if not (0 < value <= 100):
            raise HTTPException(status_code=400, detail="value (percent) ต้องอยู่ในช่วง 0–100")
        if max_discount is not None and float(max_discount) <= 0:
            raise HTTPException(status_code=400, detail="max_discount ต้องมากกว่า 0")
    else:  # fixed
        if value <= 0:
            raise HTTPException(status_code=400, detail="value (fixed) ต้องมากกว่า 0")
        max_discount = None

    if usage_limit is not None and int(usage_limit) <= 0:
        raise HTTPException(status_code=400, detail="usage_limit ต้องมากกว่า 0")

    exists = db.execute(
        text("SELECT id FROM discount_codes WHERE code = :code"),
        {"code": code},
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="โค้ดนี้ถูกใช้แล้ว")

    try:
        params = {
            "code": code,
            "type_": type_,
            "value": value,
            "max_discount": max_discount,
            "usage_limit": usage_limit,
            "status": status,
        }
        db.execute(
            text("""
                INSERT INTO discount_codes
                    (code, type, value, max_discount, usage_limit, status)
                VALUES
                    (:code, :type_, :value, :max_discount, :usage_limit, :status)
            """),
            params,
        )
        db.commit()
        return {"message": "สร้างโค้ดสำเร็จ"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"สร้างโค้ดส่วนลดล้มเหลว: {e}")

# ---------- UPDATE CODE ----------
def update_discount_code(
    db,
    code_id: int,
    type_: Optional[Literal["percent", "fixed"]] = None,
    value: Optional[float] = None,
    max_discount: Optional[float] = None,
    usage_limit: Optional[int] = None,
    status: Optional[Literal["active", "inactive"]] = None,
    new_code: Optional[str] = None,         
):
    cur = db.execute(
        text("""
            SELECT id, code, type, value, max_discount, usage_limit, status
            FROM discount_codes WHERE id = :id
        """),
        {"id": code_id},
    ).mappings().first()
    
    if not cur:
        raise HTTPException(status_code=404, detail="ไม่พบโค้ดส่วนลดนี้")

    new_type = type_ if type_ is not None else cur["type"]
    new_value = float(value) if value is not None else float(cur["value"])

    if new_type == "percent":
        new_max = float(max_discount) if max_discount is not None else (
            float(cur["max_discount"]) if cur["max_discount"] is not None else None
        )
    else:
        new_max = None

    new_limit  = int(usage_limit) if usage_limit is not None else cur["usage_limit"]
    new_status = status if status is not None else cur["status"]

    if new_type not in ("percent", "fixed"):
        raise HTTPException(status_code=400, detail="type ต้องเป็น 'percent' หรือ 'fixed'")

    if new_type == "percent":
        if not (0 < new_value <= 100):
            raise HTTPException(status_code=400, detail="value (percent) ต้องอยู่ในช่วง 0–100")
        if new_max is not None and float(new_max) <= 0:
            raise HTTPException(status_code=400, detail="max_discount ต้องมากกว่า 0")
    else:  # fixed
        if new_value <= 0:
            raise HTTPException(status_code=400, detail="value (fixed) ต้องมากกว่า 0")
        new_max = None

    if new_limit is not None and int(new_limit) <= 0:
        raise HTTPException(status_code=400, detail="usage_limit ต้องมากกว่า 0")

    fields = {
        "type": new_type,
        "value": new_value,
        "max_discount": new_max,
        "usage_limit": new_limit,
        "status": new_status,
    }

    if new_code is not None:
        normalized = new_code.strip().upper()
        if not (1 <= len(normalized) <= 32) or not re.fullmatch(r"[A-Z0-9]+", normalized):
            raise HTTPException(status_code=400, detail="รูปแบบโค้ดไม่ถูกต้อง (ต้องเป็น A–Z/0–9 ยาว 1–32 ตัว)")

        if normalized != cur["code"]:
            dup = db.execute(
                text("SELECT id FROM discount_codes WHERE code = :c AND id <> :id"),
                {"c": normalized, "id": code_id},
            ).first()
            if dup:
                raise HTTPException(status_code=400, detail="โค้ดนี้ถูกใช้อยู่แล้ว")
        fields["code"] = normalized

    # --- สร้าง SET clause แบบไดนามิก ---
    set_parts = []
    params = {"id": code_id}
    for k, v in fields.items():
        set_parts.append(f"{k} = :{k}")
        params[k] = v

    try:
        db.execute(
            text(f"UPDATE discount_codes SET {', '.join(set_parts)} WHERE id = :id"),
            params,
        )
        db.commit()
        return {"message": "อัปเดตโค้ดส่วนลดสำเร็จ"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"อัปเดตโค้ดส่วนลดล้มเหลว: {e}")

# ---------- DELETE CODE ----------
def delete_discount_code(db: Session, code_id: int):
    # ถ้าต้องการบังคับห้ามลบเมื่อมีการใช้งานแล้ว ให้เช็กตาราง redemptions ตรงนี้
    try:
        db.execute(text("DELETE FROM discount_codes WHERE id = :id"), {"id": code_id})
        db.commit()
        return {"message": "ลบโค้ดส่วนลดสำเร็จ"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"ลบโค้ดส่วนลดล้มเหลว: {e}")

# ---------- READ (by code) ----------
def get_discount_code_by_codeva(db: Session, code: str):
    row = db.execute(
        text("""
            SELECT 
                id, code, type, value, max_discount, usage_limit, status,
                created_at, updated_at
            FROM discount_codes
            WHERE code = :code
        """),
        {"code": code}
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="ไม่พบโค้ดส่วนลดนี้")

    return row

# ---------- READ (by id) ----------
def get_discount_code(db: Session, code_id: int):
    row = db.execute(
        text("""
            SELECT 
                id, code, type, value, max_discount, usage_limit, status
            FROM discount_codes
            WHERE id = :id
        """),
        {"id": code_id}
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="ไม่พบโค้ดส่วนลดนี้")

    return row

# ---------- READ (all code) ----------
def get_all_discount_codes(db: Session):
    try:
        rows = db.execute(
            text("""
                SELECT 
                    id, 
                    code, 
                    type, 
                    value, 
                    max_discount, 
                    usage_limit, 
                    status
                FROM discount_codes
                ORDER BY id DESC
            """)
        ).mappings().all()

        if not rows:
            raise HTTPException(status_code=404, detail="ยังไม่มีโค้ดส่วนลดในระบบ")

        return rows

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ไม่สามารถดึงข้อมูลโค้ดส่วนลดได้: {e}")

# ---------- READ (all code and usage) ----------
def get_all_discount_codes_with_usage(db):
    sql = text("""
        SELECT
        dc.id,
        dc.code,
        dc.type,
        dc.value,
        dc.max_discount,
        dc.usage_limit,
        dc.status,
        COALESCE(COUNT(dr.id), 0) AS used_count
        FROM discount_codes dc
        LEFT JOIN discount_redemptions dr
        ON dr.code_id = dc.id
        GROUP BY
        dc.id, dc.code, dc.type, dc.value, dc.max_discount,
        dc.usage_limit, dc.status
        ORDER BY dc.created_at DESC
    """)
    rows = db.execute(sql).mappings().all()
    return rows
