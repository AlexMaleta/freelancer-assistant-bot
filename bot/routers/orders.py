from typing import Optional

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.routers.order_stages import render_stages
from bot.states.orders import AddOrderStates, EditOrderStates
from bot.utils.utils import safe_edit_or_send
from config.constants import Statuses
from core.customers import CustomerService
from core.orders import OrderService
from database.orders import get_all_orders_by_user
from database.statuses import get_status_name, get_all_statuses
from models.orders import OrderCreate
from utils.translations import I18n
from utils.utils import normalize_phone, is_valid_email, parse_date_str, build_callback_data, parse_callback_data, \
    is_valid_deadline
from models.users import UserInDB

router = Router()
order_service = OrderService()
customer_service = CustomerService()


async def render_order_card(callback_or_message, order_id: int, user: UserInDB):
    order = order_service.get_by_id(order_id)
    if not order:
        await callback_or_message.answer(I18n.t(user.language, "no_order"), show_alert=True)
        return

    customer = customer_service.get_customer_by_id(order.customer_id)
    status = get_status_name(order.status_id, user.language)

    deadline_txt = I18n.t(user.language, "deadline")
    created_at_txt = I18n.t(user.language, "created_at")
    updated_at_txt = I18n.t(user.language, "updated_at")

    text = (
        f"📁 <b>{order.name}</b>\n"
        f"👤 <b>{customer.name}</b>\n"
        f"📝 {order.description or '–'}\n"
        f"📊 {status or '–'}\n"
        f"{deadline_txt}: {order.deadline.date() if order.deadline else '–'}\n"
        f"{created_at_txt}: {order.created_at.date() if order.created_at else '–'}\n"
        f"{updated_at_txt}: {order.updated_at.date() if order.updated_at else '–'}\n"
    )

    buttons = [[]]

    if order.status_id not in Statuses.FINAL:
        buttons += [[InlineKeyboardButton(
                text=I18n.t(user.language, "button_stages"),
                callback_data=f"order_stages:{order.id}"
            ),
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_delete"),
                callback_data=f"delete_order:{order.id}"
            )]]
        buttons += [[InlineKeyboardButton(
                text=I18n.t(user.language, "button_edit"),
                callback_data=f"edit_order:{order.id}"
            ),
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_status"),
                callback_data=f"edit_order_status:{order.id}"
            )]]
    else:
        buttons += [[InlineKeyboardButton(
                text=I18n.t(user.language, "button_stages"),
                callback_data=f"order_stages:{order.id}"
            )]]
    buttons += [[InlineKeyboardButton(
                text=I18n.t(user.language, "button_back"),
                callback_data="back_to_order_list")]]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    await safe_edit_or_send(msg, text, parse_mode="HTML", reply_markup=keyboard)
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


async def render_orders(callback_or_message, state: FSMContext, user: UserInDB):
    data = await state.get_data()
    customer_id = data.get("customer_id")
    if not customer_id:
        orders = get_all_orders_by_user(user.id)
    else:
        orders = get_all_orders_by_user(user_id=user.id, customer_id=customer_id)
    # callback or message
    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    if not orders:
        if not customer_id:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=I18n.t(user.language, "add_order"), callback_data="add_order")]
            ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=I18n.t(user.language, "add_order"), callback_data="select_customer:")]
            ])
        await safe_edit_or_send(msg, I18n.t(user.language, "no_orders"), parse_mode="HTML", reply_markup=keyboard)
    else:
        if not customer_id:
            buttons = [[InlineKeyboardButton(text=I18n.t(user.language, "add_order"), callback_data="add_order")]]
        else:
            buttons = [[InlineKeyboardButton(text=I18n.t(user.language, "add_order"), callback_data="select_customer:")]]
        buttons += [
            [InlineKeyboardButton(text=order.name, callback_data=f"order:{order.id}")]
            for order in orders
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await safe_edit_or_send(msg, I18n.t(user.language, "select_order"), parse_mode="HTML", reply_markup=keyboard)

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


@router.message(lambda msg: msg.text in ["📁 Projects", "📁 Проекты"])
async def get_orders(message: Message, state: FSMContext, user: UserInDB):
    await state.clear()
    await render_orders(message, state, user)


@router.callback_query(F.data.startswith("order:"))
async def show_order_details(callback: CallbackQuery, user: UserInDB):
    order_id = int(callback.data.split(":")[1])
    await render_order_card(callback, order_id, user)
    await callback.answer()


@router.callback_query(F.data == "back_to_order_list")
async def back_to_order_list(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    await render_orders(callback, state, user)
    await callback.answer()

@router.callback_query(F.data == "add_order")
async def start_add_order(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    from bot.routers.customers import render_customers
    customers = customer_service.get_customers_by_user(user.id)

    if not customers:
        await callback.answer(I18n.t(user.language, "order_no_customers"))
        await render_customers(callback, user)
        return

    # customer selection buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c.name, callback_data=f"select_customer:{c.id}")]
        for c in customers
    ])

    await state.set_state(AddOrderStates.waiting_for_customer)
    await callback.message.edit_text(I18n.t(user.language, "order_select_customer"), parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("select_customer:"))
async def selected_customer(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    data = await state.get_data()
    customer_id = data.get("customer_id")
    if not customer_id:
        customer_id = int(callback.data.split(":")[1])
        await state.update_data(customer_id=customer_id)
    await state.set_state(AddOrderStates.waiting_for_name)
    await callback.message.edit_text(I18n.t(user.language, "add_order_name"))
    await callback.answer()


@router.message(AddOrderStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext, user: UserInDB):
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer(I18n.t(user.language, "add_name_error"))
        return

    await state.update_data(name=name)
    await state.set_state(AddOrderStates.waiting_for_description)
    await message.answer(I18n.t(user.language, "add_description"))


@router.message(AddOrderStates.waiting_for_description)
async def get_description(message: Message, state: FSMContext, user: UserInDB):
    description = message.text.strip()
    await state.update_data(description=description)
    await state.set_state(AddOrderStates.waiting_for_deadline)
    await message.answer(I18n.t(user.language, "add_deadline"))


@router.message(AddOrderStates.waiting_for_deadline)
async def get_deadline_and_save(message: Message, state: FSMContext, user: UserInDB):
    date_str = message.text.strip()
    deadline = parse_date_str(date_str)
    if not deadline:
        await message.answer(I18n.t(user.language, "wrong_date"))
        return
    if not is_valid_deadline(deadline):
        await message.answer(I18n.t(user.language, "wrong_date_limit"))
        return

    data = await state.get_data()
    customer_id = data["customer_id"]
    name = data["name"]
    description = data["description"]
    order = OrderCreate(
        user_id=user.id,
        customer_id=customer_id,
        name=name,
        description=description,
        deadline=deadline
    )


    if order_service.create_order(order):
        await message.answer(I18n.t(user.language, "add_order_success").format(name=name),
                         parse_mode="HTML")
        await render_orders(message, state, user)
    else:
        await message.answer(I18n.t(user.language, "error_txt"))
        await render_orders(message, state, user)

    await state.clear()
    await state.update_data(customer_id=customer_id)


@router.callback_query(F.data.startswith("edit_order_status:"))
async def edit_order_status(callback: CallbackQuery, user: UserInDB):
    order_id = int(callback.data.split(":")[1])

    statuses = get_all_statuses(user.language)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=build_callback_data(action="change_order_status", status_id=status_id, order_id=order_id))]
        for status_id, label in statuses
    ])
    await callback.message.edit_text(I18n.t(user.language, "select_status"), reply_markup=keyboard)


@router.callback_query(F.data.startswith("action=change_order_status"))
async def change_order_status(callback: CallbackQuery, user: UserInDB):

    data = parse_callback_data(callback.data)
    status_id = int(data["status_id"])
    order_id = int(data["order_id"])
    # update status in DB, etc...
    if order_service.update_order_fields(order_id=order_id, status_id=status_id):
        await callback.answer(I18n.t(user.language, "status_updated"), show_alert=True)
        await render_order_card(callback, order_id, user)
    else:
        await callback.answer(I18n.t(user.language, "error_txt"), show_alert=True)
        await render_order_card(callback, order_id, user)


@router.callback_query(F.data.startswith("delete_order:"))
async def delete_order(callback: CallbackQuery, user: UserInDB):
    order_id = int(callback.data.split(":")[1])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=I18n.t(user.language, "button_yes"), callback_data=f"confirm_delete_order:{order_id}"),
            InlineKeyboardButton(text=I18n.t(user.language, "button_no"), callback_data=f"cancel_delete_order:{order_id}")
        ]
    ])

    await callback.message.edit_text(I18n.t(user.language, "order_delete"), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_order:"))
async def confirm_delete_order(callback: CallbackQuery, state, user: UserInDB):
    order_id = int(callback.data.split(":")[1])
    order = order_service.get_by_id(order_id)

    if not order:
        await callback.answer(I18n.t(user.language, "no_order"), show_alert=True)
        return

    if order_service.delete_order(order_id):
        await callback.answer(I18n.t(user.language, "order_deleted").format(name=order.name), show_alert=True)
        await render_orders(callback, state, user)
    else:
        await callback.answer(I18n.t(user.language, "error_txt"), show_alert=True)
        await render_orders(callback, state, user)


@router.callback_query(F.data.startswith("cancel_delete_order:"))
async def cancel_deletion(callback: CallbackQuery, user: UserInDB):
    order_id = int(callback.data.split(":")[1])

    await render_order_card(callback, order_id, user)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_order:"))
async def start_edit_order(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    order_id = int(callback.data.split(":")[1])
    order = order_service.get_by_id(order_id)

    if not order:
        await callback.answer(I18n.t(user.language, "no_order"), show_alert=True)
        return

    await state.update_data(order_id=order_id)
    await state.set_state(EditOrderStates.waiting_for_name)

    await callback.message.edit_text(
        I18n.t(user.language, "edit_order_name").format(name=order.name),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EditOrderStates.waiting_for_name)
async def edit_name(message: Message, state: FSMContext, user: UserInDB):
    name = message.text.strip()
    if name != "-":
        if len(name) < 2:
            await message.answer(I18n.t(user.language, "wrong_name"))
            return
        await state.update_data(name=name)

    await state.set_state(EditOrderStates.waiting_for_description)
    await message.answer(I18n.t(user.language, "edit_description"))


@router.message(EditOrderStates.waiting_for_description)
async def edit_description(message: Message, state: FSMContext, user: UserInDB):
    description = message.text.strip()
    if description != "-":
        await state.update_data(description=description)
    await state.set_state(EditOrderStates.waiting_for_deadline)
    await message.answer(I18n.t(user.language, "edit_deadline"))


@router.message(EditOrderStates.waiting_for_deadline)
async def edit_deadline_and_save(message: Message, state: FSMContext, user: UserInDB):
    date_str = message.text.strip()
    update_fields = {}

    if date_str != "-":
        deadline = parse_date_str(date_str)
        if not deadline:
            await message.answer(I18n.t(user.language, "wrong_date"))
            return
        if not is_valid_deadline(deadline):
            await message.answer(I18n.t(user.language, "wrong_date_limit"))
            return
        update_fields["deadline"] = deadline

    data = await state.get_data()

    if data.get("name"):
        update_fields["name"] = data["name"]

    if data.get("description"):
        update_fields["description"] = data["description"]


    if order_service.update_order_fields(order_id=data["order_id"], **update_fields):
        await message.answer(I18n.t(user.language, "edit_order_success"),
                         parse_mode="HTML")
        await render_orders(message, state, user)
    else:
        await message.answer(I18n.t(user.language, "error_txt"))
        await render_orders(message, state, user)

    #await state.clear()


@router.callback_query(F.data.startswith("order_stages:"))
async def show_order_stages(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await render_stages(callback, state, user)
    await callback.answer()
