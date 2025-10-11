from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class GameBase(BaseModel):
    name: str
    type_id: int
    description: str
    price: float
    image_url: str

class GameCreate(GameBase):
    pass

class GameUpdate(BaseModel):
    name: Optional[str] = None
    type_id: Optional[int] = None
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