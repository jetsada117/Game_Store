from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings  

# ใช้ DATABASE_URL จาก config
engine = create_engine(settings.DATABASE_URL, echo=True)

# session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base class สำหรับ ORM models
Base = declarative_base()
