import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile, InputMediaPhoto
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.bot.keyboards.callbacks.payment import PaymentCallback, PaymentAction
from src.bot.keyboards.user import generate_payment_status_keyboard
from src.bot.states.order_search import OrderSearchState
from src.bot.utils.scheduler_service import SchedulerService
from src.database.models import OrderSearchORM
from src.database.uow import UnitOfWork

router = Router(name=__name__)
log = logging.getLogger(__name__)

# Константы для временных интервалов напоминаний (в секундах)
REMINDER_INTERVALS = [
    timedelta(seconds=24),  # Первое напоминание через 24 часа
    *[
        timedelta(seconds=26 + i * 2) for i in range(17)
    ],  # Затем каждые 2 часа до 58 часов
]
FINAL_REMINDER_DELTA = timedelta(seconds=60)  # Финальное напоминание через 60 часов


def clear_receipt_reminders(scheduler: AsyncIOScheduler, chat_id: int) -> None:
    """Удаляет все задачи напоминаний о чеке по указанному чату"""
    for job in scheduler.get_jobs():
        if job.id.startswith(f"receipt_reminder_{chat_id}_"):
            job.remove()


class PaymentHandler:
    """Класс для обработки платежей и связанной логики"""

    @staticmethod
    async def schedule_reminders(
        scheduler: AsyncIOScheduler,
        chat_id: int,
        material_id: int,
        intervals: List[timedelta],
    ) -> None:
        """Планирует серию напоминаний о необходимости отправить чек"""
        for interval in intervals:
            scheduler.add_job(
                SchedulerService.send_input_receipt,
                "date",
                run_date=datetime.now() + interval,
                kwargs={
                    "chat_id": chat_id,
                    "material_id": material_id,
                    "message": "Пожалуйста, отправьте номер чека - инструкция в видео выше. Если не разберетесь пишите в поддержку.",
                    "state": OrderSearchState.AWATING_RECEIPT_NUMBER,
                },
                replace_existing=True,
                id=f"receipt_reminder_{chat_id}_{interval.total_seconds()}s",
            )

        # Финальное напоминание
        scheduler.add_job(
            SchedulerService.send_input_receipt,
            "date",
            run_date=datetime.now() + timedelta(minutes=5),
            kwargs={
                "chat_id": chat_id,
                "material_id": material_id,
                "message": "Важно не забыть отправить номер чека в этот диалог, иначе мы не сможем найти ваш заказ - отправим вам пустую коробку. Через 24 часа этот Бот напомнит Вам про Чек.",
                "state": OrderSearchState.AWATING_RECEIPT_NUMBER,  # Очищаем состояние после финального напоминания
            },
            replace_existing=True,
            id=f"receipt_reminder_{chat_id}_300s",
        )
        scheduler.add_job(
            SchedulerService.send_input_receipt,
            "date",
            run_date=datetime.now() + FINAL_REMINDER_DELTA,
            kwargs={
                "chat_id": chat_id,
                "material_id": material_id,
                "message": (
                    "Не получили от вас номер Чека.\n"
                    "К сожалению мы вынуждены отправить вам пустую коробку.\n"
                    "Вы можете отменить этот товар на валдбериз либо отказаться / не забирать его на ПВЗ валдбериз!\n"
                    "Хорошего дня !"
                ),
                "state": OrderSearchState.INPUT_TIME_OVER,
            },
            replace_existing=True,
            id=f"receipt_reminder_{chat_id}_final",
        )

    @staticmethod
    async def process_not_paid_order(
        call: CallbackQuery, callback_data: PaymentCallback, stage: int
    ) -> None:
        """Обрабатывает уведомление о неоплаченном заказе на разных этапах"""
        messages = {
            1: "Необходимо зайти в приложение валдберз. Найти оформленный наш с вами товар и оплатить его. "
            "Это необходимо сделать, так как нам нужен будет Чек, а чек приходит только после оплаты.",
            2: "Оплата необходима для получения чека. Без чека мы не сможем найти ваш заказ "
            "и будем вынуждены отправить пустую коробку.",
            3: "Благодарим за обращение. К сожалению, мы не сможем изготовить ваш товар. "
            "Вы можете отменить заказ в приложении Валдбериз или не забирать его с ПВЗ.",
        }
        await call.message.edit_text(
            text=messages[stage],
            reply_markup=generate_payment_status_keyboard(
                material_id=callback_data.material_id,
                show_not_paid=stage == 1,
                stage=stage + 1 if stage < 3 else None,
            ),
        )


@router.callback_query(
    PaymentCallback.filter((F.action == PaymentAction.NOT_PAY) & (F.stage == 1))
)
async def handle_not_paid_stage_1(call: CallbackQuery, callback_data: PaymentCallback):
    """Обрабатывает первый этап уведомления о неоплаченном заказе"""
    await call.message.delete()

    text = (
        "Необходимо зайти в приложение валдберз. Найти оформленный наш с вами товар и оплатить его. "
        "Это необходимо сделать, так как нам нужен будет Чек, а чек приходит только после оплаты."
    )

    await call.message.answer_media_group(
        media=[
            InputMediaPhoto(media=FSInputFile("statics/images/correct_payment.PNG")),
            InputMediaPhoto(
                media=FSInputFile("statics/images/not_correct_payment.PNG")
            ),
        ]
    )

    await call.message.answer(
        text=text,
        reply_markup=generate_payment_status_keyboard(
            material_id=callback_data.material_id, show_not_paid=True, stage=2
        ),
    )


@router.callback_query(
    PaymentCallback.filter((F.action == PaymentAction.NOT_PAY) & (F.stage == 2))
)
async def handle_not_paid_stage_2(call: CallbackQuery, callback_data: PaymentCallback):
    """Обрабатывает второй этап уведомления о неоплаченном заказе"""
    await PaymentHandler.process_not_paid_order(call, callback_data, stage=2)


@router.callback_query(
    PaymentCallback.filter((F.action == PaymentAction.NOT_PAY) & (F.stage == 3))
)
async def handle_not_paid_stage_3(call: CallbackQuery, callback_data: PaymentCallback):
    """Обрабатывает третий этап уведомления о неоплаченном заказе"""
    await PaymentHandler.process_not_paid_order(call, callback_data, stage=3)


@router.callback_query(PaymentCallback.filter(F.action == PaymentAction.PAY))
async def handle_payment_confirmation(
    call: CallbackQuery,
    callback_data: PaymentCallback,
    state: FSMContext,
    # scheduler: AsyncIOScheduler,
):
    """Обрабатывает подтверждение оплаты и запускает напоминания"""
    await state.set_state(OrderSearchState.AWATING_RECEIPT_NUMBER)
    await state.update_data(material_id=callback_data.material_id)

    # await PaymentHandler.schedule_reminders(
    #     scheduler=scheduler,
    #     chat_id=call.from_user.id,
    #     material_id=callback_data.material_id,
    #     intervals=REMINDER_INTERVALS,
    # )

    await call.message.delete()

    await call.message.answer_video(
        video=FSInputFile("statics/videos/find_receipt_number_guide.mp4"),
        caption="Отлично! Через 24 часа в приложении Валдбериз придет чек. "
        "Пожалуйста, отправьте номер чека в этот бот. "
        "Инструкцию по поиску чека смотрите в видео.",
    )


@router.message(OrderSearchState.AWATING_RECEIPT_NUMBER, F.text, ~F.photo)
async def handle_receipt_number_input(
    message: Message,
    state: FSMContext,
    uow: UnitOfWork,
    # scheduler: AsyncIOScheduler,
):
    """Обрабатывает ввод номера чека от пользователя"""

    if len(message.text.split(".")) < 3:
        log.info(
            "Неверный формат номера чека: %s - %s", message.from_user.id, message.text
        )
        return await message.answer(
            text="Номер чека должен быть в формате 8130114057298979999.0.0",
        )

    state_data = await state.get_data()
    material_id = state_data.get("material_id")
    receipt_number = message.text.strip()

    processing_msg = await message.answer(
        "Обрабатываю данные. Пожалуйста, подождите..."
    )

    await asyncio.sleep(2)

    order_search = OrderSearchORM(
        material_id=material_id,
        search_type="RECEIPT_NUMBER",
        filters={"receipt_number": receipt_number},
    )

    uow.session.add(order_search)
    await uow.session.commit()

    await state.clear()

    # clear_receipt_reminders(scheduler, message.from_user.id)

    await processing_msg.edit_text(
        text=(f"Чек <code>{receipt_number}</code> принят в обработку, ожидайте...")
    )


# @router.message(OrderSearchState.INPUT_TIME_OVER, F.text)
# async def handle_input_time_over(message: Message, state: FSMContext):
#     """Обрабатывает сообщения при превышении времени ожидания ввода номера чека"""
#     await state.clear()
#     await message.answer(
#         text=(
#             "Вы отправили номер чека слишком поздно, на ваш пвз уже отправлена пустая коробка."
#         ),
#         reply_markup=get_catalog_button_keyboard(button_text="Перезаказать"),
#     )
