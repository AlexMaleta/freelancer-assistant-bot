from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.user_states import EditUserStates, EditUserStates
from bot.utils.utils import safe_edit_or_send
from core.users import UserService
from database.users import get_user_by_id
from models.users import UserInDB
from utils.translations import I18n
from utils.utils import is_valid_email

router = Router()
user_service = UserService()


async def render_user_card(callback_or_message, user: UserInDB):

    user = get_user_by_id(user.id)

    lang = user.language
    yes = I18n.t(lang, "yes")
    no = I18n.t(lang, "no")

    notify_email = yes if user.notify_email else no
    notify_telegram = yes if user.notify_telegram else no

    text = (
        f"👤 <b>{user.name or '–'}</b>\n"
        f"<b>{I18n.t(lang, 'language')}:</b> {lang}\n"
        f"📧 <b>Email:</b> {user.email or '–'}\n"
        f"<b>{I18n.t(lang, 'notify_email')}:</b> {notify_email}\n"
        f"<b>{I18n.t(lang, 'notify_telegram')}:</b> {notify_telegram}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=I18n.t(lang, "edit_profile"), callback_data="edit_profile")],
        [InlineKeyboardButton(text=I18n.t(lang, "choose_language"), callback_data="edit_language")],
        [InlineKeyboardButton(text=I18n.t(lang, "change_notify_email"), callback_data="change_notify_email")],
        [InlineKeyboardButton(text=I18n.t(lang, "change_notify_telegram"), callback_data="change_notify_telegram")]
    ])

    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    await safe_edit_or_send(msg, text, parse_mode="HTML", reply_markup=keyboard)
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


@router.message(F.text.in_({"⚙️ Настройки", "⚙️ Settings"}))
async def show_user_settings(message: Message, state: FSMContext, user: UserInDB):
    await state.clear()
    await render_user_card(message, user)


@router.callback_query(F.data == "change_notify_email")
async def change_notify_email(callback: CallbackQuery, user: UserInDB):
    lang = user.language

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=I18n.t(lang, "yes"), callback_data="set_notify_email:1"),
            InlineKeyboardButton(text=I18n.t(lang, "no"), callback_data="set_notify_email:0")
        ]
    ])

    await callback.message.edit_text(
        I18n.t(lang, "change_notify_email"),
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_notify_email:"))
async def set_notify_email(callback: CallbackQuery, user: UserInDB):
    value = bool(int(callback.data.split(":")[1]))
    user_service.update_notifications(user.id, notify_email=value)

    await callback.answer(I18n.t(user.language, "setting_updated"))
    await render_user_card(callback.message, user)


@router.callback_query(F.data == "change_notify_telegram")
async def change_notify_telegram(callback: CallbackQuery, user: UserInDB):
    lang = user.language

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=I18n.t(lang, "yes"), callback_data="set_notify_telegram:1"),
            InlineKeyboardButton(text=I18n.t(lang, "no"), callback_data="set_notify_telegram:0")
        ]
    ])

    await callback.message.edit_text(
        I18n.t(lang, "change_notify_telegram"),
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_notify_telegram:"))
async def set_notify_telegram(callback: CallbackQuery, user: UserInDB):
    value = bool(int(callback.data.split(":")[1]))
    user_service.update_notifications(user.id, notify_telegram=value)

    await callback.answer(I18n.t(user.language, "setting_updated"))

    await render_user_card(callback.message, user)


@router.callback_query(F.data == "edit_language")
async def edit_language(callback: CallbackQuery, user: UserInDB):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇸 English", callback_data="set_lang:en"),
            InlineKeyboardButton(text="Русский", callback_data="set_lang:ru")
        ]
    ])
    await callback.message.edit_text("🌍 Выберите язык интерфейса:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("set_lang:"))
async def set_language(callback: CallbackQuery, user: UserInDB):
    lang = callback.data.split(":")[1]

    user_service.update_language(user.id, lang)

    await callback.answer(I18n.t(lang, "setting_updated"))
    user.language = lang
    await render_user_card(callback.message, user)


@router.callback_query(F.data == "edit_profile")
async def start_edit_profile(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    await state.set_state(EditUserStates.waiting_for_name)
    await callback.message.edit_text(I18n.t(user.language, "add_new_name"))
    await callback.answer()


@router.message(EditUserStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext, user: UserInDB):
    name = message.text.strip()

    if not name or len(name) < 2 or len(name) > 30 or not name.replace(" ", "").isalpha():
        await message.answer(I18n.t(user.language, "wrong_name"))
        return

    await state.update_data(name=name)
    await state.set_state(EditUserStates.waiting_for_email)
    await message.answer(I18n.t(user.language, "add_email"))


@router.message(EditUserStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext, user: UserInDB):
    email = message.text.strip()
    if email != "-":
        if not is_valid_email(email):
            await message.answer(I18n.t(user.language, "email_error"))
            return

    data = await state.get_data()
    name = data.get("name")

    user_service.update_email(user.id, email)
    if name:
        user_service.update_user_name(user.id, name)

    await state.clear()
    await message.answer(I18n.t(user.language, "setting_updated"))
    await render_user_card(message, user)