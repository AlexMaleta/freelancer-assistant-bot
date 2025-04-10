from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.routers.checklist_items import render_checklist
from bot.states.order_stages import AddStageStates, EditStageStates
from bot.utils.utils import safe_edit_or_send
from config.constants import Statuses
from core.order_stages import OrderStageService
from core.orders import OrderService
from database.statuses import get_status_name, get_all_statuses
from models.order_stages import StageCreate
from models.users import UserInDB
from utils.translations import I18n
from utils.utils import parse_date_str, build_callback_data, parse_callback_data, is_valid_deadline

router = Router()
order_service = OrderService()
stage_service = OrderStageService()


async def render_stage_card(callback_or_message, stage_id: int, user: UserInDB):
    stage = stage_service.get_stage_by_id(stage_id)
    if not stage:
        await callback_or_message.answer(I18n.t(user.language, "no_stage"), show_alert=True)
        return

    order = order_service.get_by_id(stage.order_id)
    status = get_status_name(stage.status_id, user.language)

    deadline_txt = I18n.t(user.language, "deadline")
    created_at_txt = I18n.t(user.language, "created_at")
    updated_at_txt = I18n.t(user.language, "updated_at")

    text = (
        f"📁 <b>{stage.name}</b>\n"
        f"👤 <b>{order.name}</b>\n"
        f"📝 {stage.description or '–'}\n"
        f"📊 {status or '–'}\n"
        f"{deadline_txt}: {stage.deadline.date() if stage.deadline else '–'}\n"
        f"{created_at_txt}: {stage.created_at.date() if stage.created_at else '–'}\n"
        f"{updated_at_txt}: {stage.updated_at.date() if stage.updated_at else '–'}\n"
    )

    buttons = [[]]

    if stage.status_id not in Statuses.FINAL:
        buttons += [[
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_checklist"),
                callback_data=f"project_checklist:{stage.id}"
            ),
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_delete"),
                callback_data=f"delete_stage:{stage.id}"
            )
        ]]
        buttons += [[InlineKeyboardButton(
                text=I18n.t(user.language, "button_edit"),
                callback_data=f"edit_stage:{stage.id}"
            ),
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_status"),
                callback_data=f"edit_stage_status:{stage.id}"
            )]]
    else:
        buttons += [[
            InlineKeyboardButton(
                text=I18n.t(user.language, "button_checklist"),
                callback_data=f"project_checklist:{stage.id}"
            )]]
    buttons += [[InlineKeyboardButton(
                text=I18n.t(user.language, "button_back"),
                callback_data="back_to_stages_list")
    ]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    await safe_edit_or_send(msg, text, parse_mode="HTML", reply_markup=keyboard)
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


async def render_stages(callback_or_message, state: FSMContext, user: UserInDB):
    data = await state.get_data()
    order_id = data.get("order_id")
    order = order_service.get_by_id(order_id)
    stages = stage_service.get_stages_by_order(order_id)

    msg = callback_or_message.message if hasattr(callback_or_message, "message") else callback_or_message
    if not stages:
        buttons = [[]]
        if order.status_id not in Statuses.FINAL:
            buttons += [[InlineKeyboardButton(text=I18n.t(user.language, "add_stage"), callback_data="add_stage")]]
        buttons += [[InlineKeyboardButton(text=I18n.t(user.language, "button_back"),callback_data="back_to_order")]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await safe_edit_or_send(msg, I18n.t(user.language, "no_stages"), parse_mode="HTML", reply_markup=keyboard)
    else:
        buttons = [[]]
        if order.status_id not in Statuses.FINAL:
            buttons = [[InlineKeyboardButton(text=I18n.t(user.language, "add_stage"), callback_data="add_stage")]]
        buttons += [
            [InlineKeyboardButton(text=stage.name, callback_data=f"stage:{stage.id}")]
            for stage in stages
        ]
        buttons += [[InlineKeyboardButton(text=I18n.t(user.language, "button_back"),
                                         callback_data="back_to_order")]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await safe_edit_or_send(msg, I18n.t(user.language, "select_stage"), parse_mode="HTML", reply_markup=keyboard)

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()


@router.callback_query(F.data.startswith("stage:"))
async def show_stage_details(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    stage_id = int(callback.data.split(":")[1])
    await render_stage_card(callback, stage_id, user)
    await callback.answer()


@router.callback_query(F.data == "back_to_order")
async def back_to_order(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    from bot.routers.orders import render_order_card
    data = await state.get_data()
    order_id = data.get("order_id")
    await render_order_card(callback, order_id, user)
    await callback.answer()


@router.callback_query(F.data == "back_to_stages_list")
async def back_to_stages_list(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    await render_stages(callback, state, user)
    await callback.answer()

@router.callback_query(F.data == "add_stage")
async def start_add_stage(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    await state.set_state(AddStageStates.waiting_for_name)
    await callback.message.edit_text(I18n.t(user.language, "add_stage_name"))
    await callback.answer()


@router.message(AddStageStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext, user: UserInDB):
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer(I18n.t(user.language, "add_name_error"))
        return

    await state.update_data(name=name)
    await state.set_state(AddStageStates.waiting_for_description)
    await message.answer(I18n.t(user.language, "add_description"))


@router.message(AddStageStates.waiting_for_description)
async def get_description(message: Message, state: FSMContext, user: UserInDB):
    description = message.text.strip()
    await state.update_data(description=description)
    await state.set_state(AddStageStates.waiting_for_deadline)
    await message.answer(I18n.t(user.language, "add_deadline"))


@router.message(AddStageStates.waiting_for_deadline)
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
    order_id = data.get("order_id")

    stage = StageCreate(
        order_id=data["order_id"],
        name=data["name"],
        description=data["description"],
        deadline=deadline
    )


    if stage_service.create_stage(stage):
        await message.answer(I18n.t(user.language, "add_stage_success"),
                         parse_mode="HTML")
        await render_stages(message, state, user)
    else:
        await message.answer(I18n.t(user.language, "error_txt"))
        await render_stages(message, state, user)

    await state.clear()
    await state.update_data(order_id=order_id)


@router.callback_query(F.data.startswith("edit_stage_status:"))
async def edit_stage_status(callback: CallbackQuery, user: UserInDB):
    stage_id = int(callback.data.split(":")[1])

    statuses = get_all_statuses(user.language)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=build_callback_data(action="change_stage_status", status_id=status_id, stage_id=stage_id))]
        for status_id, label in statuses
    ])
    await callback.message.edit_text(I18n.t(user.language, "select_status"), reply_markup=keyboard)


@router.callback_query(F.data.startswith("action=change_stage_status"))
async def change_stage_status(callback: CallbackQuery, user: UserInDB):

    data = parse_callback_data(callback.data)
    status_id = int(data["status_id"])
    stage_id = int(data["stage_id"])
    # update status in DB, etc...
    if stage_service.update_stage(stage_id=stage_id, status_id=status_id):
        await callback.answer(I18n.t(user.language, "status_updated"), show_alert=True)
        await render_stage_card(callback, stage_id, user)
    else:
        await callback.answer(I18n.t(user.language, "error_txt"), show_alert=True)
        await render_stage_card(callback, stage_id, user)


@router.callback_query(F.data.startswith("delete_stage:"))
async def delete_stage(callback: CallbackQuery, user: UserInDB):
    stage_id = int(callback.data.split(":")[1])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=I18n.t(user.language, "button_yes"), callback_data=f"confirm_delete_stage:{stage_id}"),
            InlineKeyboardButton(text=I18n.t(user.language, "button_no"), callback_data=f"cancel_delete_stage:{stage_id}")
        ]
    ])

    await callback.message.edit_text(I18n.t(user.language, "stage_delete"), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_stage:"))
async def confirm_delete_stage(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    stage_id = int(callback.data.split(":")[1])
    stage = stage_service.get_stage_by_id(stage_id)

    if not stage:
        await callback.answer(I18n.t(user.language, "no_stage"), show_alert=True)
        return

    if stage_service.delete_stage(stage_id):
        await callback.answer(I18n.t(user.language, "stage_deleted").format(name=stage.name), show_alert=True)
        await render_stages(callback, state, user)
    else:
        await callback.answer(I18n.t(user.language, "error_txt"), show_alert=True)
        await render_stages(callback, state, user)


@router.callback_query(F.data.startswith("cancel_delete_stage:"))
async def cancel_deletion(callback: CallbackQuery, user: UserInDB):
    stage_id = int(callback.data.split(":")[1])

    await render_stage_card(callback, stage_id, user)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_stage:"))
async def start_edit_stage(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    stage_id = int(callback.data.split(":")[1])
    stage = stage_service.get_stage_by_id(stage_id)

    if not stage:
        await callback.answer(I18n.t(user.language, "no_stage"), show_alert=True)
        return

    await state.update_data(stage_id=stage_id)
    await state.set_state(EditStageStates.waiting_for_name)

    await callback.message.edit_text(
        I18n.t(user.language, "edit_stage_name").format(name=stage.name),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EditStageStates.waiting_for_name)
async def edit_name(message: Message, state: FSMContext, user: UserInDB):
    name = message.text.strip()
    if name != "-":
        if len(name) < 2:
            await message.answer(I18n.t(user.language, "wrong_name"))
            return
        await state.update_data(name=name)

    await state.set_state(EditStageStates.waiting_for_description)
    await message.answer(I18n.t(user.language, "edit_description"))


@router.message(EditStageStates.waiting_for_description)
async def edit_description(message: Message, state: FSMContext, user: UserInDB):
    description = message.text.strip()
    if description != "-":
        await state.update_data(description=description)
    await state.set_state(EditStageStates.waiting_for_deadline)
    await message.answer(I18n.t(user.language, "edit_deadline"))


@router.message(EditStageStates.waiting_for_deadline)
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

    order_id = data.get("order_id")

    if data.get("name"):
        update_fields["name"] = data["name"]

    if data.get("description"):
        update_fields["description"] = data["description"]


    if stage_service.update_stage(stage_id=data["stage_id"], **update_fields):
        await message.answer(I18n.t(user.language, "edit_stage_success"),
                         parse_mode="HTML")
        await render_stages(message, state, user)
    else:
        await message.answer(I18n.t(user.language, "error_txt"))
        await render_stages(message, state, user)

    await state.clear()
    await state.update_data(order_id=order_id)


@router.callback_query(F.data.startswith("project_checklist:"))
async def show_project_checklist(callback: CallbackQuery, state: FSMContext, user: UserInDB):
    stage_id = int(callback.data.split(":")[1])
    await state.update_data(stage_id=stage_id)
    await render_checklist(callback, state, user)
    await callback.answer()
