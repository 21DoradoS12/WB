import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.handlers import register_all_routers
from src.bot.middlewares import register_all_middlewares
from src.core.config.settings import settings
from src.core.setup_logging import setup_logging

log = logging.getLogger(__name__)


async def main():
    storage = RedisStorage.from_url(
        url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
        connection_kwargs={
            "retry_on_timeout": True,
            "socket_timeout": 10,
            "socket_connect_timeout": 5,
            "max_connections": 20,
            "health_check_interval": 30,
        },
    )

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dp = Dispatcher(storage=storage)

    register_all_middlewares(dp=dp)
    register_all_routers(dp=dp)

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        log.info("Бот остановлен пользователем!")
    except Exception as ex:
        log.error("Ошибка при запуске бота: %s", ex, exc_info=True)


if __name__ == "__main__":
    setup_logging(service_name="bot")
    asyncio.run(main())
