from aiogram.fsm.state import StatesGroup, State

class AddItem(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()

class EditItem(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_status = State()