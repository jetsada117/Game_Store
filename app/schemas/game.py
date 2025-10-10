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

class GameResponse(GameBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class GameCategory(BaseModel):
    id: int
    name: str