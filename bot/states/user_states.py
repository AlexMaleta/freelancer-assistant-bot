from aiogram.fsm.state import StatesGroup, State

class RegistrationUserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
class EditUserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()