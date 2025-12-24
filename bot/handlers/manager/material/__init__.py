from aiogram import Router

from . import bind_to_assembly_task, info


def register_routers() -> Router:
    router = Router()

    router.include_router(bind_to_assembly_task.router)
    router.include_router(info.router)

    return router
