from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

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
            "processed_at": datetime.now(),
        }
    )

    db.commit()

    row = db.execute(
        text("SELECT id, wallet_balance FROM users WHERE id = :id"),
        {"id": user_id}
    ).mappings().first()

    return row


def get_transactions_by_user_id(db: Session, user_id: int):
    sql = text("""
        SELECT id, user_id, type, order_id, amount, status, processed_at
        FROM transactions
        WHERE user_id = :uid
        ORDER BY processed_at DESC
    """)

    params = {"uid": user_id}

    row = db.execute(sql, params).all()
    return row