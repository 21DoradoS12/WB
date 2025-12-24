from aiogram import Dispatcher

from . import admins
from . import base, materials, order_search, manager


def register_all_routers(dp: Dispatcher):
    # dp.message.filter(IsPrivateChat())
    # dp.callback_query.filter(IsPrivateChat())

    dp.include_router(admins.register_routers())
    dp.include_router(manager.register_routers())
    dp.include_router(base.register_routers())
    dp.include_router(materials.register_routers())
    dp.include_router(order_search.register_routers())
