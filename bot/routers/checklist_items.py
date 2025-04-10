from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.states.checklist_items import AddItem, EditItem
from bot.utils.utils import safe_edit_or_send
from config.constants import Statuses
from core.checklist_items import ChecklistService
from core.order_stages import OrderStageService, checklist_service
from database.statuses import get_status_name, get_all_statuses
from models.checklist_items import ChecklistItemCreate
from models.users import UserInDB
from utils.translations import I18n
from utils.utils import build_callback_data, parse_callback_data

router = Router()
stage_service = OrderStageService()
checklist_service = ChecklistService()


async def render_item(callback_or_message, item_id: int, user: UserInDB):
    item = checklist_service.get_item_by_id(item_id)
    if not item:
        await callback_or_message.answer(I18n.t(user.language, "no_item"), show_alert=True)
        return

    stage = stage_service.get_stage_by_id(item.stage_id)
    status = get_status_name(item.status_id, user.language)

    created_at_txt = I18n.t(user.language, "created_at")
    updated_at_txt = I18n.t(user.language, "updated_at")

    text = (
        f"📁 <b>{item.name}</b>\n"
        f"👤 <b>{stage.name}</b>\n"
        f"📝 {item.description or '–'}\n"
        f"📊 {status or '–'}\n"
        f"{created_at_txt}: {item.created_at.date() if item.created_at else '–'}\n"
        f"{updated_at_txt}: {item.updated_at.date() if item.updated_at else '–'}\n"
    )
    buttons =[[]]

    if item.status_id not in Statuses.FINAL:
        buttons += [[InlineKeyboardButton(
            text=I18n.t(user.language, "button_delete"),
            callback_data=f"delete_item:{item.id}"
        )]]
        buttons += [[InlineKeyboardButton(
            text=I18n.t(user.language, "button_edit"),
            callback_data=f"edit_item:{item.id}"
        ),
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_status"),
                callback_data=f"edit_item_status:{item.id}"
            )]]
    buttons += [[InlineKeyboardButton(
        text=I18n.t(user.language, "button_back"),
        callback_data="back_to_items_list"
    )]]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    await safe_edit_or_send(msg, text, parse_mode="HTML", reply_markup=keyboard)
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


async def render_checklist(callback_or_message, state: FSMContext, user: UserInDB):
    data = await state.get_data()
    stage_id = data.get("stage_id")
    stage = stage_service.get_stage_by_id(stage_id)
    items = checklist_service.get_items_by_stage(stage_id)

    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    if not items:
        buttons = [[]]
        if stage.status_id not in Statuses.FINAL:
            buttons += [[InlineKeyboardButton(text=I18n.t(user.language, "add_item"), callback_data="add_item")]]
        buttons += [[InlineKeyboardButton(text=I18n.t(user.language, "button_back"), callback_data="back_to_stage")]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await safe_edit_or_send(msg, I18n.t(user.language, "no_items"), parse_mode="HTML", reply_markup=keyboard)
    else:
        buttons = [[]]
        if stage.status_id not in Statuses.FINAL:
            buttons = [[InlineKeyboardButton(text=I18n.t(user.language, "add_item"), callback_data="add_item")]]
        buttons += [
            [InlineKeyboardButton(text=item.name, callback_data=f"item:{item.id}")]
            for item in items
        ]
        buttons += [[InlineKeyboardButton(text=I18n.t(user.language, "button_back"),
                                          callback_data="back_to_stage")]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await safe_edit_or_send(msg, I18n.t(user.language, "select_item"), parse_mode="HTML", reply_markup=keyboard)

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


@router.callback_query(F.data.startswith("item:"))
async def show_item_details(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    item_id = int(callback.data.split(":")[1])
    await render_item(callback, item_id, user)
    await callback.answer()


@router.callback_query(F.data == "back_to_stage")
async def back_to_stage(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    from bot.routers.order_stages import render_stage_card
    data = await state.get_data()
    stage_id = data.get("stage_id")
    await render_stage_card(callback, stage_id, user)
    await callback.answer()


@router.callback_query(F.data == "back_to_items_list")
async def back_to_items_list(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    await render_checklist(callback, state, user)
    await callback.answer()


@router.callback_query(F.data == "add_item")
async def start_add_item(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    await state.set_state(AddItem.waiting_for_name)
    await callback.message.edit_text(I18n.t(user.language, "add_item_name"))
    await callback.answer()


@router.message(AddItem.waiting_for_name)
async def get_name(message: Message, state: FSMContext, user: UserInDB):
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer(I18n.t(user.language, "add_name_error"))
        return

    await state.update_data(name=name)
    await state.set_state(AddItem.waiting_for_description)
    await message.answer(I18n.t(user.language, "add_description"))


@router.message(AddItem.waiting_for_description)
async def get_description(message: Message, state: FSMContext, user: UserInDB):
    description = message.text.strip()
    data = await state.get_data()
    order_id = data.get("order_id")
    stage_id = data.get("stage_id")

    item = ChecklistItemCreate(
        stage_id=data["stage_id"],
        name=data["name"],
        description=description
    )

    if checklist_service.create_item(item):
        await message.answer(I18n.t(user.language, "add_item_success"),
                             parse_mode="HTML")
        await render_checklist(message, state, user)
    else:
        await message.answer(I18n.t(user.language, "error_txt"))
        await render_checklist(message, state, user)

    await state.clear()
    await state.update_data(order_id=order_id)
    await state.update_data(stage_id=stage_id)


@router.callback_query(F.data.startswith("edit_item_status:"))
async def edit_item_status(callback: CallbackQuery, user: UserInDB):
    item_id = int(callback.data.split(":")[1])

    statuses = get_all_statuses(user.language)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label,
                              callback_data=build_callback_data(action="change_item_status", status_id=status_id,
                                                                item_id=item_id))]
        for status_id, label in statuses
    ])
    await callback.message.edit_text(I18n.t(user.language, "select_status"), reply_markup=keyboard)


@router.callback_query(F.data.startswith("action=change_item_status"))
async def change_item_status(callback: CallbackQuery, user: UserInDB):
    data = parse_callback_data(callback.data)
    status_id = int(data["status_id"])
    item_id = int(data["item_id"])
    # update status in DB, etc...
    if checklist_service.update_item(item_id=item_id, status_id=status_id):
        await callback.answer(I18n.t(user.language, "status_updated"), show_alert=True)
        await render_item(callback, item_id, user)
    else:
        await callback.answer(I18n.t(user.language, "error_txt"), show_alert=True)
        await render_item(callback, item_id, user)


@router.callback_query(F.data.startswith("delete_item:"))
async def delete_item(callback: CallbackQuery, user: UserInDB):
    item_id = int(callback.data.split(":")[1])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=I18n.t(user.language, "button_yes"),
                                 callback_data=f"confirm_delete_item:{item_id}"),
            InlineKeyboardButton(text=I18n.t(user.language, "button_no"), callback_data=f"cancel_delete_item:{item_id}")
        ]
    ])

    await callback.message.edit_text(I18n.t(user.language, "item_delete"), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_item:"))
async def confirm_delete_item(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    item_id = int(callback.data.split(":")[1])
    item = checklist_service.get_item_by_id(item_id)

    if not item:
        await callback.answer(I18n.t(user.language, "no_item"), show_alert=True)
        return

    if checklist_service.delete_item(item_id):
        await callback.answer(I18n.t(user.language, "item_deleted").format(name=item.name), show_alert=True)
        await render_checklist(callback, state, user)
    else:
        await callback.answer(I18n.t(user.language, "error_txt"), show_alert=True)
        await render_checklist(callback, state, user)


@router.callback_query(F.data.startswith("cancel_delete_item:"))
async def cancel_deletion(callback: CallbackQuery, user: UserInDB):
    item_id = int(callback.data.split(":")[1])

    await render_item(callback, item_id, user)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_item:"))
async def start_edit_item(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    item_id = int(callback.data.split(":")[1])
    item = checklist_service.get_item_by_id(item_id)

    if not item:
        await callback.answer(I18n.t(user.language, "no_item"), show_alert=True)
        return

    await state.update_data(item_id=item_id)
    await state.set_state(EditItem.waiting_for_name)

    await callback.message.edit_text(
        I18n.t(user.language, "edit_item_name").format(name=item.name),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EditItem.waiting_for_name)
async def edit_name(message: Message, state: FSMContext, user: UserInDB):
    name = message.text.strip()
    if name != "-":
        if len(name) < 2:
            await message.answer(I18n.t(user.language, "wrong_name"))
            return
        await state.update_data(name=name)

    await state.set_state(EditItem.waiting_for_description)
    await message.answer(I18n.t(user.language, "edit_description"))


@router.message(EditItem.waiting_for_description)
async def edit_description(message: Message, state: FSMContext, user: UserInDB):
    description = message.text.strip()
    update_fields = {}
    data = await state.get_data()

    order_id = data.get("order_id")
    stage_id = data.get("stage_id")

    if data.get("name"):
        update_fields["name"] = data["name"]

    update_fields["description"] = description

    if checklist_service.update_item(item_id=data["item_id"], **update_fields):
        await message.answer(I18n.t(user.language, "edit_item_success"),
                             parse_mode="HTML")
        await render_checklist(message, state, user)
    else:
        await message.answer(I18n.t(user.language, "error_txt"))
        await render_checklist(message, state, user)

    await state.clear()
    await state.update_data(order_id=order_id)
    await state.update_data(stage_id=stage_id)

