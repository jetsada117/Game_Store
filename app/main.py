from fastapi import FastAPI
from app.controller.index import router as index_router
from app.controller.user import router as user_router
from app.db import models
from app.db.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="My API", version="1.0.0")

app.include_router(index_router)
app.include_router(user_router)
