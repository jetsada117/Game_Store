from pydantic import BaseModel, Field
from typing import Optional

# -----------------------------
# Base schema (ใช้ร่วม)
# -----------------------------
class UserBase(BaseModel):
    username: str
    email: str 


# -----------------------------
# Schema สำหรับการสร้างผู้ใช้
# -----------------------------
class UserCreate(UserBase):
    password: str
    img_url: str


# -----------------------------
# Schema สำหรับการตอบกลับ
# -----------------------------
class UserResponse(UserBase):
    id: int
    img_url: str
    role: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    wallet_balance: Optional[float] = None


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1)