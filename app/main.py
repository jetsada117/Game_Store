from fastapi import FastAPI
from app.controller.index import router as index_router

app = FastAPI(title="My API", version="1.0.0")

app.include_router(index_router)