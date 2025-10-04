from fastapi import APIRouter, Response

router = APIRouter()

@router.get("/")
def index():
    return "Hello Game Store"

@router.get("/", include_in_schema=False)
def health_get():
    return {"status": "ok"}

@router.head("/", include_in_schema=False)
def health_head():
    return Response(status_code=200)