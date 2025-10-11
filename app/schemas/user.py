from pydantic import BaseModel, Field
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str 
    password: str
    img_url: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str 
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


class MoneyUpdate(BaseModel):
    id: int
    wallet_balance: float

    class Config:
        from_attributes = True