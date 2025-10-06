from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings  

engine = create_engine(
    settings.DATABASE_URL,          # ex: mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
    echo=False,
    pool_pre_ping=True,             # ✅ เช็คว่า connection ยังใช้ได้ก่อนทุกครั้ง
    pool_recycle=280,               # ✅ รีไซเคิลก่อน wait_timeout (เช่นถ้า wait_timeout = 300s)
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 10},   # เผื่อเชื่อมช้า
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
