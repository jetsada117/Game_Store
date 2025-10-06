from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from grpc import Status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.crud import user as crud_user
from app.db.dependency import get_db
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return crud_user.get_users(db)

@router.post("/", response_model=UserResponse)
async def create_user_with_image(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),              
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if image.content_type not in {"image/png", "image/jpeg"}:
        raise HTTPException(status_code=400, detail="Only PNG/JPEG are allowed")

    user_in = UserCreate(
        username=username,
        email=email,
        password=password,
        img_url=""
    )

    created = crud_user.create_user_with_file(db, user_in, image) 
    if not created:
        raise HTTPException(status_code=400, detail="Create user failed")
    return created


@router.put("/{user_id}")
def update_user_info(
    user_id: int,
    username: str = Form(None),
    email: str = Form(None),
    image_file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    payload = UserUpdate(
        username=username,
        email=email,
        
    )

    try:
        if image_file:
            user = crud_user.update_profile_with_file(db, user_id, payload, image_file)
        else:
            user = crud_user.update_profile(db, user_id, payload)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "User updated successfully", "data": user}

    except HTTPException as e:
        if e.status_code == 409:
            return JSONResponse(
                status_code=Status.HTTP_409_CONFLICT,
                content={"message": "อีเมลนี้ถูกใช้แล้ว"}
            )
        raise