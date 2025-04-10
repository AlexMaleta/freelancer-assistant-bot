from aiogram.fsm.state import StatesGroup, State

class AddStageStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()

class EditStageStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_status = State()