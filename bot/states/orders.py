from aiogram.fsm.state import StatesGroup, State

class AddOrderStates(StatesGroup):
    waiting_for_customer = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()

class EditOrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_status = State()