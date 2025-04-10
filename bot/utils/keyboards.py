
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from utils.translations import I18n


async def get_language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇬🇧 English"), KeyboardButton(text="Русский")]
        ],
        resize_keyboard=True
    )

async def main_keyboard(language: str):
    buttons = I18n.t(language, "main_buttons")
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=buttons[0]), KeyboardButton(text=buttons[1])],
            [KeyboardButton(text=buttons[2]), KeyboardButton(text=buttons[3])]
        ],
        resize_keyboard=True
    )
