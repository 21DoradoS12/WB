from aiogram import Dispatcher
from aiogram_album.count_check_middleware import CountCheckAlbumMiddleware

from src.bot.middlewares.uow_middleware import UnitOfWorkMiddleware
from .user_data_middleware import UserDataMiddleware


def register_all_middlewares(dp: Dispatcher):
    dp.message.middleware.register(CountCheckAlbumMiddleware())

    dp.update.middleware.register(UnitOfWorkMiddleware())

    dp.message.middleware.register(UserDataMiddleware())
    dp.callback_query.middleware.register(UserDataMiddleware())
