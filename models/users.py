from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    telegram_id: int
    name: str
    language: str = "en"
    email: Optional[str] = "-"
    notify_email: bool = False
    notify_telegram: bool = True


class UserCreate(UserBase):
    pass


class UserInDB(UserBase):
    id: int