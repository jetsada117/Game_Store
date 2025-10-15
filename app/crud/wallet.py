from datetime import datetime, timedelta, timezone
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


def purchase_games(db: Session, user_id: int, game_ids: Iterable[int]):
    """
    ซื้อหลายเกมในครั้งเดียว
    - ตรวจ user, เกม, และการเป็นเจ้าของเดิม
    - คำนวณยอดรวมและหักเงิน wallet
    - สร้าง order + order_items + transactions
    - ออก user_game_licenses
    คืน: ข้อมูลคำสั่งซื้อ (order) และรายการเกมที่ซื้อ
    """
    # เตรียมข้อมูลเบื้องต้น
    game_ids = [int(g) for g in game_ids if g is not None]
    if not game_ids:
        raise HTTPException(status_code=400, detail="ต้องระบุ game_ids อย่างน้อย 1 รายการ")
    game_ids = sorted(set(game_ids))  # กันซ้ำ

    try:
        # ----- เริ่มทรานแซกชัน
        # ล็อกแถวผู้ใช้ไว้เพื่อกัน race condition ตอนหักเงิน
        user = db.execute(
            text("SELECT id, wallet_balance FROM users WHERE id = :uid FOR UPDATE"),
            {"uid": user_id}
        ).mappings().first()
        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบบัญชีผู้ใช้")

        wallet_balance = float(user["wallet_balance"] or 0)

        # 1) เกมที่ขอซื้อมีจริงไหม
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

        # 2) เช็กสิทธิ์เดิม กันซื้อซ้ำ
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

        # 3) คำนวณยอดรวม (snapshot ราคา)
        subtotal = sum(float(g["price"]) for g in games)
        discount = 0.0
        total = subtotal - discount

        if wallet_balance < total:
            raise HTTPException(status_code=400, detail="ยอดเงินในวอลเล็ตไม่เพียงพอ")

        # 4) สร้าง order (pending)
        order_id = db.execute(
            text("""
                INSERT INTO orders
                    (user_id, subtotal_amount, discount_amount, total_amount, status, created_at, updated_at)
                VALUES
                    (:uid, :subtotal, :discount, :total, 'pending', :now, :now)
            """),
            {"uid": user_id, "subtotal": subtotal, "discount": discount, "total": total, "now": datetime.now()}
        ).lastrowid

        # 5) ใส่ order_items (snapshot unit_price)
        db.execute(
            text("""
                INSERT INTO order_items (order_id, game_id, unit_price, quantity, created_at)
                VALUES (:oid, :gid, :price, 1, :now)
            """),
            [
                {"oid": order_id, "gid": int(g["id"]), "price": float(g["price"]), "now": datetime.now()}
                for g in games
            ]
        )

        # 6) หักเงิน wallet
        new_balance = wallet_balance - total
        db.execute(
            text("UPDATE users SET wallet_balance = :bal WHERE id = :uid"),
            {"bal": new_balance, "uid": user_id}
        )

        # 7) บันทึกธุรกรรม (transactions)
        db.execute(
            text("""
                INSERT INTO transactions (user_id, order_id, type, amount, status, processed_at)
                VALUES (:uid, :oid, 'purchase', :amt, 'SUCCESS', :processed_at)
            """),
            {"uid": user_id, "oid": order_id, "amt": total, "processed_at": function.thai_date()}
        )

        # 8) ออก license ให้ผู้ใช้
        db.execute(
            text("""
                INSERT INTO user_game_licenses (user_id, game_id, order_id, acquired_at)
                VALUES (:uid, :gid, :oid, :now)
                ON DUPLICATE KEY UPDATE order_id = VALUES(order_id), acquired_at = VALUES(acquired_at)
            """),
            [{"uid": user_id, "gid": int(g["id"]), "oid": order_id, "now": datetime.now()} for g in games]
        )

        # 9) ปิดคำสั่งซื้อ
        db.execute(text("UPDATE orders SET status='fulfilled', updated_at=:now WHERE id=:oid"),
                   {"now": datetime.now(), "oid": order_id})

        db.commit()

        # 10) คืนข้อมูลคำสั่งซื้อ
        order = [{"game_id": int(g["id"]), "name": g["name"]} for g in games]
        return order

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดระหว่างทำรายการ: {e}")
    

def purchase_one_game(db: Session, user_id: int, game_id: int) -> dict:
    """ซื้อเกมเดี่ยว สะดวกๆ"""
    return purchase_games(db, user_id, [game_id])


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
    type_: Literal["percent", "fixed"] = "percent",
    value: float = 0,
    max_discount: Optional[float] = None,
    status: Literal["active", "inactive"] = "active",
):
    code = function._gen_code(6).upper().strip()

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
        return {"message": "สร้างโค้ดสำเร็จ", "code": code}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"สร้างโค้ดส่วนลดล้มเหลว: {e}")

# ---------- UPDATE CODE ----------
def update_discount_code(
    db: Session,
    code_id: int,
    type_: Optional[Literal["percent", "fixed"]] = None,
    value: Optional[float] = None,
    max_discount: Optional[float] = None,
    usage_limit: Optional[int] = None,
    status: Optional[Literal["active", "inactive"]] = None,
):
    cur = db.execute(
        text("""SELECT id, type, value, max_discount, usage_limit, status
                FROM discount_codes WHERE id = :id"""),
        {"id": code_id},
    ).mappings().first()
    if not cur:
        raise HTTPException(status_code=404, detail="ไม่พบโค้ดส่วนลดนี้")

    new_type = type_ if type_ is not None else cur["type"]
    new_value = float(value) if value is not None else float(cur["value"])
    # ถ้าเป็น percent ให้คง/อัปเดต max_discount; ถ้าเป็น fixed ให้เป็น None
    if new_type == "percent":
        new_max = float(max_discount) if max_discount is not None else (
            float(cur["max_discount"]) if cur["max_discount"] is not None else None
        )
    else:  # fixed
        new_max = None

    new_limit = int(usage_limit) if usage_limit is not None else cur["usage_limit"]
    new_status = status if status is not None else cur["status"]

    # validate
    if new_type not in ("percent", "fixed"):
        raise HTTPException(status_code=400, detail="type ต้องเป็น 'percent' หรือ 'fixed'")
    if new_type == "percent":
        if not (0 < new_value <= 100):
            raise HTTPException(status_code=400, detail="value (percent) ต้องอยู่ในช่วง 0–100")
        if new_max is not None and float(new_max) <= 0:
            raise HTTPException(status_code=400, detail="max_discount ต้องมากกว่า 0")
    else:
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
        return {"message": "อัปเดตโค้ดส่วนลดสำเร็จ", "id": code_id}
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
                id, code, type, value, max_discount, usage_limit, status,
                created_at, updated_at
            FROM discount_codes
            WHERE id = :id
        """),
        {"id": code_id}
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="ไม่พบโค้ดส่วนลดนี้")

    return row
