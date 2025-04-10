from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StageBase(BaseModel):
    order_id: int
    name: str
    description: Optional[str] = None
    status_id: Optional[int] = 1
    deadline: Optional[datetime] = None


class StageCreate(StageBase):
    pass


class StageInDB(StageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
