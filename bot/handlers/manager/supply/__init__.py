from aiogram import Router

from . import show_supply, supply_actions


def register_routers() -> Router:
    router = Router()

    router.include_router(show_supply.router)
    router.include_router(supply_actions.router)

    return router
