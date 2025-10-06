from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controller import auth
from app.controller.index import router as index_router
from app.controller.user import router as user_router
from app.db import models
from app.db.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="My API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # <-- ให้ทุกโดเมนเข้าถึงได้
    allow_credentials=True,    # ถ้าไม่จำเป็นใช้ cookie, สามารถเปลี่ยนเป็น False
    allow_methods=["*"],       # อนุญาตทุก method เช่น GET, POST, PUT, DELETE
    allow_headers=["*"],       # อนุญาตทุก header เช่น Authorization, Content-Type
)

app.include_router(index_router)
app.include_router(user_router)
app.include_router(auth.router) 
