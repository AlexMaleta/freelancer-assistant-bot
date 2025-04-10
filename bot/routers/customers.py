from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.routers.orders import render_orders
from bot.states.customer_states import AddCustomerStates, EditCustomerStates
from bot.utils.utils import safe_edit_or_send
from utils.translations import I18n
from utils.utils import normalize_phone, is_valid_email
from core.customers import CustomerService
from database.customers import get_all_customers_by_user
from models.customers import CustomerCreate
from models.users import UserInDB

router = Router()
customer_service = CustomerService()


async def render_customer_card(callback_or_message, customer_id: int, user: UserInDB):
    customer = customer_service.get_customer_by_id(customer_id)
    if not customer:
        await callback_or_message.answer(I18n.t(user.language, "no_customer"), show_alert=True)
        return

    text = (
        f"👤 <b>{customer.name}</b>\n"
        f"📞 {customer.phone or '–'}\n"
        f"✉️ {customer.email or '–'}\n"
        f"📝 {customer.notes or '–'}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_orders"),
                callback_data=f"customer_orders:{customer.id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_edit"),
                callback_data=f"edit_customer:{customer.id}"
            ),
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_delete"),
                callback_data=f"delete_customer:{customer.id}"
            )
        ]
    ])

    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    await safe_edit_or_send(msg, text, parse_mode="HTML", reply_markup=keyboard)
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


async def render_customers(callback_or_message, user: UserInDB):
    customers = get_all_customers_by_user(user.id)
    # callback or message
    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    if not customers:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=I18n.t(user.language, "add_customer"), callback_data="add_customer")]
        ])
        await safe_edit_or_send(msg, I18n.t(user.language, "no_customers"), parse_mode="HTML", reply_markup=keyboard)
    else:
        buttons = [[InlineKeyboardButton(text=I18n.t(user.language, "add_customer"), callback_data="add_customer")]]
        buttons += [
            [InlineKeyboardButton(text=c.name, callback_data=f"customer:{c.id}")]
            for c in customers
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await safe_edit_or_send(msg, I18n.t(user.language, "select_customer"), parse_mode="HTML", reply_markup=keyboard)

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


@router.message(lambda msg: msg.text in ["👤 Клиенты", "👤 Customers"])
async def get_customers(message: Message, state: FSMContext, user: UserInDB):
    await state.clear()
    await render_customers(message, user)


@router.callback_query(lambda c: c.data.startswith("customer:"))
async def show_customer_details(callback: CallbackQuery, user: UserInDB):
    customer_id = int(callback.data.split(":")[1])
    await render_customer_card(callback, customer_id, user)


@router.callback_query(F.data.startswith("customer_orders:"))
async def show_customer_orders(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    customer_id = int(callback.data.split(":")[1])
    await state.update_data(customer_id=customer_id)
    await render_orders(callback, state, user)
    await callback.answer()


@router.callback_query(F.data == "add_customer")
async def start_add_customer(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    await state.set_state(AddCustomerStates.waiting_for_name)
    await callback.message.edit_text(I18n.t(user.language, "add_customer_name"))
    await callback.answer()


@router.message(AddCustomerStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext, user: UserInDB):
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer(I18n.t(user.language, "add_customer_name_error"))
        return

    await state.update_data(name=name)
    await state.set_state(AddCustomerStates.waiting_for_phone)
    await message.answer(I18n.t(user.language, "add_customer_phone"))


@router.message(AddCustomerStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext, user: UserInDB):
    phone = message.text.strip()
    if phone == "-":
        await state.update_data(phone=None)
    else:
        if not normalize_phone(phone):
            await message.answer(I18n.t(user.language, "customer_phone_error"))
            return
        await state.update_data(phone=phone)
    await state.set_state(AddCustomerStates.waiting_for_email)
    await message.answer(I18n.t(user.language, "add_email"))


@router.message(AddCustomerStates.waiting_for_email)
async def get_email(message: Message, state: FSMContext, user: UserInDB):
    email = message.text.strip()
    if email == "-":
        await state.update_data(email=None)
    else:
        if not is_valid_email(email):
            await message.answer(I18n.t(user.language, "email_error"))
            return
        await state.update_data(email=email)
    await state.set_state(AddCustomerStates.waiting_for_notes)
    await message.answer(I18n.t(user.language, "add_note"))


@router.message(AddCustomerStates.waiting_for_notes)
async def get_notes_and_save(message: Message, state: FSMContext, user: UserInDB):
    notes = message.text.strip()
    data = await state.get_data()

    new_customer = CustomerCreate(
        user_id=user.id,
        name=data["name"],
        phone=data.get("phone"),
        email=data.get("email"),
        notes=None if notes == "-" else notes
    )

    if customer_service.create_customer(new_customer):
        await message.answer(I18n.t(user.language, "add_customer_success").format(name=data["name"]),
                         parse_mode="HTML")
        await render_customers(message, user)
    else:
        await message.answer(I18n.t(user.language, "error_txt"))
        await render_customers(message, user)

    #await state.clear()


@router.callback_query(F.data.startswith("delete_customer:"))
async def confirm_delete_customer(callback: CallbackQuery, user: UserInDB):
    customer_id = int(callback.data.split(":")[1])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=I18n.t(user.language, "button_yes"), callback_data=f"confirm_delete_customer:{customer_id}"),
            InlineKeyboardButton(text=I18n.t(user.language, "button_no"), callback_data=f"cancel_delete_customer:{customer_id}")
        ]
    ])

    await callback.message.edit_text(I18n.t(user.language, "customer_delete"), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_customer:"))
async def delete_customer(callback: CallbackQuery, user: UserInDB):
    customer_id = int(callback.data.split(":")[1])
    customer = customer_service.get_customer_by_id(customer_id)

    if not customer:
        await callback.answer(I18n.t(user.language, "no_customer"), show_alert=True)
        return

    if customer_service.delete_customer(customer_id):
        await callback.answer(I18n.t(user.language, "customer_deleted").format(name=customer.name), show_alert=True)
        await render_customers(callback, user)
    else:
        await callback.answer(I18n.t(user.language, "error_txt"), show_alert=True)
        await render_customers(callback, user)

@router.callback_query(F.data.startswith("cancel_delete_customer:"))
async def cancel_deletion(callback: CallbackQuery, user: UserInDB):
    customer_id = int(callback.data.split(":")[1])

    await render_customer_card(callback, customer_id, user)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_customer:"))
async def start_edit_customer(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    customer_id = int(callback.data.split(":")[1])
    customer = customer_service.get_customer_by_id(customer_id)

    if not customer or customer.user_id != user.id:
        await callback.answer(I18n.t(user.language, "no_customer"), show_alert=True)
        return

    await state.update_data(customer_id=customer_id)
    await state.set_state(EditCustomerStates.waiting_for_name)

    await callback.message.edit_text(
        I18n.t(user.language, "edit_customer_name").format(name=customer.name),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(EditCustomerStates.waiting_for_name)
async def edit_name(message: Message, state: FSMContext, user: UserInDB):
    text = message.text.strip()
    if text != "-":
        if len(text) < 2:
            await message.answer(I18n.t(user.language, "wrong_name"))
            return
        await state.update_data(name=text)

    await state.set_state(EditCustomerStates.waiting_for_phone)
    await message.answer(I18n.t(user.language, "edit_customer_phone"))


@router.message(EditCustomerStates.waiting_for_phone)
async def edit_phone(message: Message, state: FSMContext, user: UserInDB):
    text = message.text.strip()

    if text != "-":
        phone = normalize_phone(text)
        if not phone:
            await message.answer(I18n.t(user.language, "customer_phone_error"))
            return
        await state.update_data(phone=phone)

    await state.set_state(EditCustomerStates.waiting_for_email)
    await message.answer(I18n.t(user.language, "edit_email"))


@router.message(EditCustomerStates.waiting_for_email)
async def edit_email(message: Message, state: FSMContext, user: UserInDB):
    email = message.text.strip()

    if email != "-":
        if not is_valid_email(email):
            await message.answer(I18n.t(user.language, "email_error"))
            return
        await state.update_data(email=email)

    await state.set_state(EditCustomerStates.waiting_for_notes)
    await message.answer(I18n.t(user.language, "edit_note"))


@router.message(EditCustomerStates.waiting_for_notes)
async def edit_notes_and_save(message: Message, state: FSMContext, user: UserInDB):
    notes = message.text.strip()
    data = await state.get_data()

    if customer_service.update_customer(customer_id=data["customer_id"],
                                     name=data.get("name"),
                                     phone=data.get("phone"),
                                     email=data.get("email"),
                                     notes=None if notes == "-" else notes):
        await message.answer(I18n.t(user.language, "status_updated"), show_alert=True)
        await render_customer_card(message, data["customer_id"], user)
    else:
        await message.answer(I18n.t(user.language, "error_txt"), show_alert=True)
        await render_customer_card(message, data["customer_id"], user)
    await message.answer(I18n.t(user.language, "edit_customer_success"))
    #await state.clear()
