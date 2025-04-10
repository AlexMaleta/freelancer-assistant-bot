import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, \
    FSInputFile
from aiogram.filters import Command

from bot.states.contact import ContactDevState
from bot.states.user_states import RegistrationUserStates
from bot.utils.keyboards import get_language_keyboard, main_keyboard
from config import config
from utils.notification_utils import send_email
from utils.utils import is_valid_email
from utils.translations import I18n
from database.users import create_user, get_user_by_telegram_id
from models.users import UserCreate, UserInDB

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    user = get_user_by_telegram_id(user_id)

    if not user or not user.name:
        await message.answer(
            "🌍 Please choose your language / Пожалуйста, выбери язык:",
            reply_markup=await get_language_keyboard()
        )
        return

    await message.answer(I18n.t(user.language, "welcome_back"), reply_markup=await main_keyboard(user.language))


@router.message(lambda msg: msg.text in ["🇬🇧 English", "Русский"])
async def language_selection_handler(message: Message, state: FSMContext):
    lang_map = {
        "🇬🇧 English": "en",
        "Русский": "ru"
    }
    language = lang_map[message.text]
    await state.update_data(language=language, telegram_id=message.from_user.id)

    await message.answer(I18n.t(language, "what_name"), reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegistrationUserStates.waiting_for_name)


@router.message(RegistrationUserStates.waiting_for_name)
async def receive_name(message: Message, state: FSMContext):
    data = await state.get_data()
    language = data["language"]
    telegram_id = data["telegram_id"]

    name = message.text.strip()

    #Validate name
    if not name or len(name) < 2 or len(name) > 30 or not name.replace(" ", "").isalpha():
        await message.answer(I18n.t(language, "wrong_name"))
        return

    await state.update_data(language=language, telegram_id=message.from_user.id, name=name)

    await message.answer(I18n.t(language, "add_email"), reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegistrationUserStates.waiting_for_email)


@router.message(RegistrationUserStates.waiting_for_email)
async def receive_name(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    language = data["language"]
    telegram_id = data["telegram_id"]

    email = message.text.strip()

    if email != "-":
        if not is_valid_email(email):
            await message.answer(I18n.t(language, "email_error"))
            return

    # Create user
    user = UserCreate(name=name, language=language, telegram_id=telegram_id, email=email)
    user_id = create_user(user)

    messages = I18n.t(user.language, "thank_registering").format(name=name)

    await message.answer(
        messages,
        reply_markup=await main_keyboard(language)
    )

    await state.clear()


@router.message(lambda msg: msg.text in ["❓ Помощь", "❓ Help"])
async def help_message(message: Message, user: UserInDB, state: FSMContext):
    await state.clear()

    lang = user.language
    text = I18n.t(lang, "help_text")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=I18n.t(lang, "get_guide"), callback_data="get_guide")],
        [InlineKeyboardButton(text=I18n.t(lang, "contact_dev"), callback_data="contact_dev")]
    ])

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "contact_dev")
async def ask_for_message(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    await state.set_state(ContactDevState.message)
    await callback.message.edit_text(I18n.t(user.language, "send_message_prompt"))
    await callback.answer()

@router.callback_query(F.data == "get_guide")
async def get_guide(callback: CallbackQuery, state: FSMContext, user: UserInDB):

    await callback.message.answer(I18n.t(user.language, "get_guide_txt"))
    if user.language == "en":
        if os.path.exists("files/User Guide.pdf"):
            await callback.message.answer_document(FSInputFile("files/User Guide.pdf"))
    else:
        if os.path.exists("files/Руководство пользователя.pdf"):
            await callback.message.answer_document(FSInputFile("files/Руководство пользователя.pdf"))
    await callback.answer()


@router.message(ContactDevState.message)
async def process_user_message(message: Message, state: FSMContext, user: UserInDB):
    text = message.text.strip()
    await state.clear()

    subject = f"Feedback from the user #{user.id}"
    full_message = f"🧑 User: {user.name or '–'}\n📨 Email: {user.email or '–'}\n\n💬 Message:\n{text}"

    send_email(
        to_address=config.ADMIN_EMAIL,
        message=full_message,
        subject=subject
    )

    await message.answer(I18n.t(user.language, "thanks_feedback"))
