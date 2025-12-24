from aiogram.fsm.state import StatesGroup, State


class TemplateFormStates(StatesGroup):
    WaitingStep = State()
    Confirmed = State()
