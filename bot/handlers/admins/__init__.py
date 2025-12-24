from aiogram import Router

from . import check_file_id, cancel, generate_template


def register_routers() -> Router:
    router = Router()

    router.include_router(cancel.router)
    router.include_router(check_file_id.router)
    router.include_router(generate_template.router)

    return router
