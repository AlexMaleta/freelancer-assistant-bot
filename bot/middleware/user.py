from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from database.users import get_user_by_telegram_id
from models.users import UserInDB


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        tg_user = event.from_user
        if not tg_user:
            return await handler(event, data)

        user: UserInDB = get_user_by_telegram_id(tg_user.id)

        data["user"] = user
        return await handler(event, data)
