from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChecklistItemBase(BaseModel):
    stage_id: int
    name: str
    description: Optional[str] = None
    status_id: Optional[int] = 1


class ChecklistItemCreate(ChecklistItemBase):
    pass


class ChecklistItemInDB(ChecklistItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
