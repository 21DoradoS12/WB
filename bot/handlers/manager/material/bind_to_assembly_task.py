import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.application.exceptions.material_exceptions import MaterialBindingError
from src.application.use_cases.material.bind_material_to_assembly_task import (
    BindMaterialToAssemblyTaskUseCase,
)
from src.bot.keyboards.callbacks.material import MaterialActionCallback
from src.bot.states import ManagerStates
from src.database.uow import UnitOfWork

router = Router()
log = logging.getLogger(__name__)


@router.callback_query(MaterialActionCallback.filter("bind_assembly" == F.action))
async def get_assembly_task_id(
    call: CallbackQuery,
    state: FSMContext,
    callback_data: MaterialActionCallback,
):
    await state.clear()
    await state.set_state(ManagerStates.bind_material)
    await state.set_data({"material_id": callback_data.material_id})
    await call.message.answer("Напишите номер сборочного задания.")


@router.message(ManagerStates.bind_material)
async def bind_material_to_assembly_task(
    message: Message,
    uow: UnitOfWork,
    state: FSMContext,
):
    try:
        assembly_task_id = int(message.text)
    except ValueError:
        await message.answer("Сборочное задание должно состоять из цифр")
        return

    state_data = await state.get_data()
    material_id = state_data.get("material_id")

    use_case = BindMaterialToAssemblyTaskUseCase(
        material_repo=uow.material,
        wb_order_repo=uow.wb_order,
        wb_assembly_task_repo=uow.wb_assembly_task,
        wb_article_repo=uow.wb_article,
    )

    try:
        await use_case.execute(
            material_id=material_id, assembly_task_id=assembly_task_id
        )
        await message.answer(
            f"✅ Материал #{material_id} успешно связан со сборкой #{assembly_task_id}"
        )
        await state.clear()
    except MaterialBindingError as e:
        await message.answer(f"⚠️ {e}")
        return
    except Exception as e:
        log.error(
            "Произошла непредвиденная ошибка во время связывания заказа: %s",
            e,
            exc_info=True,
        )
        await message.answer("Произошла ошибка, повторите попытку.")
        await state.clear()
