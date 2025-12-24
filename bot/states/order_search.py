from aiogram.fsm.state import StatesGroup, State


class OrderSearchState(StatesGroup):
    AWAITING_PHOTO = State()
    AWAITING_COUNTRY = State()
    AWAITING_SENDER_CITY = State()
    AWAITING_RECIPIENT_CITY = State()
    AWATING_RECEIPT_NUMBER = State()
    INPUT_TIME_OVER = State()
