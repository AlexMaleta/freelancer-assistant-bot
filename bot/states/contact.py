from aiogram.fsm.state import StatesGroup, State

class ContactDevState(StatesGroup):
    message = State()
