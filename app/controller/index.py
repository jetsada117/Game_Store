from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.get("/")
def index():
    return PlainTextResponse("Hello Game Store")

@router.get("/", include_in_schema=False)
def health_get():
    return {"status": "ok"}

@router.head("/", include_in_schema=False)
def health_head():
    return Response(status_code=200)