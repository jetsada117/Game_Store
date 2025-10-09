import datetime
from typing import Optional
from pydantic import BaseModel

class GameBase(BaseModel):
    name: str
    type_id: int
    description: Optional[str] = None
    price: float
    release_date: Optional[datetime.date] = None
    image_url: Optional[str] = None

class GameCreate(GameBase):
    pass

class GameResponse(GameBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True