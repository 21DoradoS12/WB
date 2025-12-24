from aiogram import Router

from . import (
    send_material,
    category_selection,
    upload_material,
    template_selection,
    confirm,
)


def register_routers() -> Router:
    router = Router()

    router.include_router(send_material.router)
    router.include_router(category_selection.router)
    router.include_router(template_selection.router)
    router.include_router(upload_material.router)
    router.include_router(confirm.router)

    return router
