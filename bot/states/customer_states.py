from aiogram.fsm.state import StatesGroup, State

class AddCustomerStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()
    waiting_for_notes = State()

class EditCustomerStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()
    waiting_for_notes = State()