from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.middleware.user import UserMiddleware
from bot.routers import all_routers
from config.config import token

bot = Bot(token=token)
dp = Dispatcher(storage=MemoryStorage())

dp.message.middleware(UserMiddleware())
dp.callback_query.middleware(UserMiddleware())


async def main():
    for router in all_routers:
        dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

