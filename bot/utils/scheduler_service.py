import logging
from typing import Optional

from aiogram import Bot
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.keyboards.user import get_support_button_keyboard


class SchedulerService:
    _bot_instance: Optional[Bot] = None
    _bot_storage: Optional[RedisStorage] = None

    @classmethod
    def set_bot(cls, bot: Bot, storage: RedisStorage):
        cls._bot_instance = bot
        cls._bot_storage = storage

    @classmethod
    async def send_input_receipt(
        cls, chat_id: int, order_id: int, message: str, state: State | None = None
    ):
        if cls._bot_instance is None:
            logging.error("Bot instance not set!")
            return
        try:
            storage_key = StorageKey(
                bot_id=cls._bot_instance.id,
                chat_id=chat_id,
                user_id=chat_id,
            )

            if state:
                await cls._bot_storage.set_state(
                    key=storage_key,
                    state=state,
                )

            await cls._bot_storage.update_data(
                key=storage_key, data={"order_id": order_id}
            )

            await cls._bot_instance.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=get_support_button_keyboard(),
            )
        except Exception as e:
            logging.error(f"Notification error: {e}")
