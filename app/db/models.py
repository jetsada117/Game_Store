from sqlalchemy import Column, Integer, String
from app.db.database import Base


# ไม่จำเป็นสำหรับ raw sql 
# ใช้สำหรับ ORM
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
