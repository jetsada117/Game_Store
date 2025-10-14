from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

class GameBase(BaseModel):
    name: str
    category_id: int
    description: str
    price: float
    image_url: str

class GameCreate(GameBase):
    pass

class GameUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    price: Optional[float] = None

class GameResponse(BaseModel):
    id: int
    name: str
    category_name: str
    description: Optional[str]
    price: float
    release_date: Optional[str]
    image_url: Optional[str]

    class Config:
        from_attributes = True

class GameCategory(BaseModel):
    id: int
    name: str


class DiscountCreate(BaseModel):
    type_: Literal["percent", "fixed"] = "percent"
    value: float = 0
    max_discount: Optional[float] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    usage_limit: Optional[int] = None
    status: Literal["active", "inactive"] = "active"