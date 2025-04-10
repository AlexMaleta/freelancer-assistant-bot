from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationBase(BaseModel):
    user_id: int
    entity_type: str    # 'order' or 'stage'
    entity_id: int
    notification_type: str = "deadline"   # 'deadline' and else
    sent_at: datetime
    channel: str = "telegram"   # 'telegram' or 'email'
    message: Optional[str] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationInDB(NotificationBase):
    id: int
