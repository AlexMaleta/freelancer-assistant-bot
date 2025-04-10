from aiogram.exceptions import TelegramBadRequest


async def safe_edit_or_send(msg, text, **kwargs):
    try:
        await msg.edit_text(text, **kwargs)
    except TelegramBadRequest:
        await msg.answer(text, **kwargs)