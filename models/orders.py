from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderBase(BaseModel):
    user_id: int
    customer_id: int
    name: str
    description: Optional[str] = None
    status_id: Optional[int] = 1
    deadline: Optional[datetime] = None


class OrderCreate(OrderBase):
    pass


class OrderInDB(OrderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
