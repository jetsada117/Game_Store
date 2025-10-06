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
    allow_origins=[
        "http://localhost:4200",         
        "https://game-store-7bbq.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(index_router)
app.include_router(user_router)
app.include_router(auth.router) 
