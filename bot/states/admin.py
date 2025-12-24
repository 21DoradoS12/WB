from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    waiting_for_file_to_get_id = State()
