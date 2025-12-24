import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineQuery,
    InputTextMessageContent,
    InlineQueryResultArticle,
    InputMediaPhoto,
    FSInputFile,
)
from sqlalchemy import select

from src.bot.keyboards.callbacks.city import CityCb
from src.bot.keyboards.callbacks.country import CountryCallback
from src.bot.keyboards.callbacks.link_material_order import LinkMaterialToOrderCallback
from src.bot.keyboards.user import (
    generate_payment_status_keyboard,
    generate_country_kb,
    get_city_kb,
    get_city_select_kb,
)
from src.bot.states.order_search import OrderSearchState
from src.database.models import OrderSearchORM, CityORM
from src.database.uow import UnitOfWork
from src.infrastructure.ocr.tesseract import process_image_with_configs

router = Router(name=__name__)


@router.callback_query(LinkMaterialToOrderCallback.filter())
async def link_material_to_order(
    call: CallbackQuery,
    callback_data: LinkMaterialToOrderCallback,
    uow: UnitOfWork,
    state: FSMContext,
):
    await call.answer()

    active_search = await uow.order_search.get_active_search_by_material_id(
        material_id=callback_data.material_id
    )
    if active_search:
        await call.message.answer(
            "⏳ Поиск по этому заказу уже запущен, пожалуйста, подождите завершения."
        )
        return

    order_matched = await uow.wb_order.get_order_by_material_id(
        callback_data.material_id
    )
    if order_matched:
        await call.message.answer(
            "❗️ Этот заказ уже связан с другим заказом и не может участвовать в новом поиске."
        )
        return

    await state.update_data(material_id=callback_data.material_id)
    await state.set_state(OrderSearchState.AWAITING_PHOTO)

    await call.message.answer_photo(
        photo=FSInputFile("statics/images/order_confirmation_example.jpg"),
        caption="Отправьте такой скриншот детализации времени вашего заказа",
    )


@router.message(OrderSearchState.AWAITING_PHOTO, F.photo, ~F.media_group_id)
async def process_photo_and_prompt_country(
    message: Message, bot: Bot, uow: UnitOfWork, state: FSMContext
):
    processing = await message.answer("Обрабатываю фото...")
    file_id = message.photo[-1].file_id
    photo_bytes = (await bot.download(file_id)).read()

    state_data = await state.get_data()
    upload_photo_error = state_data.get("upload_photo_error", 0)

    order_date = await asyncio.to_thread(process_image_with_configs, photo_bytes)

    if not order_date:
        print(upload_photo_error)
        upload_photo_error += 1
        await state.update_data(upload_photo_error=upload_photo_error)

        if upload_photo_error >= 3:
            intro_text = "Отлично, полдела сделано!"
            await message.answer(text=intro_text)

            await asyncio.sleep(2)

            # Запрос об оплате заказа
            question_text = "Вы оплатили заказ или будете оплачивать его на пункте выдачи Wildberries?"
            reply_markup = generate_payment_status_keyboard(
                material_id=state_data.get("material_id"),
                show_not_paid=True,
                stage=1,
            )
            return await message.answer(text=question_text, reply_markup=reply_markup)

        return await processing.edit_text(
            "‼️ Ошибка при распознавании фото, попробуйте еще раз."
        )

    await state.update_data(photo_id=file_id)

    await processing.edit_text("✅ Фото успешно обработано.")
    countries = await uow.country.get_countries()

    await state.set_state(OrderSearchState.AWAITING_COUNTRY)
    await state.update_data(wb_order_date=str(order_date))

    await message.answer(
        "Выберите страну оформления заказа:",
        reply_markup=generate_country_kb(countries),
    )


@router.callback_query(
    OrderSearchState.AWAITING_COUNTRY,
    CountryCallback.filter(F.action == "select"),
)
async def process_country_selection(
    call: CallbackQuery,
    state: FSMContext,
    uow: UnitOfWork,
    callback_data: CountryCallback,
    bot: Bot,
):
    country = await uow.country.get_country_by_id(callback_data.id)
    await state.update_data(country_id=country.id)

    if country.name == "Россия":
        await state.set_state(OrderSearchState.AWAITING_SENDER_CITY)

        photo_paths = [
            "statics/images/city_input_guide_1.jpg",
            "statics/images/city_input_guide_2.jpg",
            "statics/images/city_input_guide_3.jpg",
        ]

        media_group = [
            (
                InputMediaPhoto(
                    media=FSInputFile(path), caption="Пример как выбрать город"
                )
                if i == 0
                else InputMediaPhoto(media=FSInputFile(path))
            )
            for i, path in enumerate(photo_paths)
        ]

        await bot.send_media_group(
            chat_id=call.from_user.id,
            media=media_group,
        )
        await call.message.delete()

        await call.message.answer(
            text="Выберите город из которого совершаете заказ:",
            reply_markup=get_city_kb(),
        )
        return

    data = await state.get_data()
    order_datetime = datetime.strptime(data["wb_order_date"], "%Y-%m-%d %H:%M:%S")

    adjusted_order_time = order_datetime - timedelta(hours=int(country.utc_offset))

    order_search = OrderSearchORM(
        material_id=data.get("material_id"),
        search_type="COUNTRY",
        filters={
            "country": country.name,
            "order_datetime": str(adjusted_order_time),
        },
    )

    order_search = await uow.order_search.create_order_search(order_search)

    await call.message.edit_text(
        text=(
            f"✅ Ваш заказ принят в обработку!\n"
            f"🔍 Мы начали поиск, это может занять некоторое время.\n"
            f"🆔 Идентификатор поиска: #{order_search.id}\n"
            f"⏱ Максимальное время ожидания — 2 часа.\n"
            f"Спасибо за терпение! 🚀"
        )
    )


@router.inline_query(OrderSearchState.AWAITING_SENDER_CITY)
@router.inline_query(OrderSearchState.AWAITING_RECIPIENT_CITY)
async def provide_city_suggestions(query: InlineQuery, uow: UnitOfWork):
    query_text = query.query.strip()
    if not query_text:
        return

    offset = int(query.offset) if query.offset else 0
    limit = 15

    stmt = (
        select(CityORM)
        .where(CityORM.name.ilike(f"%{query_text}%"))
        .offset(offset)
        .limit(limit)
    )
    result = await uow.session.execute(stmt)
    cities = result.scalars().all()

    if not cities:
        return

    articles = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=city.name,
            description=city.region,
            input_message_content=InputTextMessageContent(
                message_text=f"{city.region} {city.name}"
            ),
            reply_markup=get_city_select_kb(city.id),
        )
        for city in cities
    ]

    next_offset = str(offset + limit) if len(cities) == limit else ""
    await query.answer(
        articles, cache_time=1, is_personal=True, next_offset=next_offset
    )


@router.callback_query(
    OrderSearchState.AWAITING_SENDER_CITY, CityCb.filter(F.action == "select")
)
async def process_sender_city_selection(
    call: CallbackQuery, callback_data: CityCb, state: FSMContext, bot: Bot
):
    await state.update_data(sender_city_id=callback_data.city_id)
    await state.set_state(OrderSearchState.AWAITING_RECIPIENT_CITY)

    await bot.edit_message_reply_markup(
        inline_message_id=call.inline_message_id, reply_markup=None
    )

    await call.bot.send_message(
        chat_id=call.from_user.id,
        text="Выберите город получателя:",
        reply_markup=get_city_kb(),
    )


@router.callback_query(
    OrderSearchState.AWAITING_RECIPIENT_CITY,
    CityCb.filter(F.action == "select"),
)
async def finalize_order(
    call: CallbackQuery,
    callback_data: CityCb,
    state: FSMContext,
    bot: Bot,
    uow: UnitOfWork,
):
    data = await state.get_data()
    recipient_city_id = callback_data.city_id

    sender_city = await uow.city.get_city_by_id(data["sender_city_id"])
    recipient_city = await uow.city.get_city_by_id(recipient_city_id)
    country = await uow.country.get_country_by_id(data["country_id"])
    order_datetime = datetime.strptime(data["wb_order_date"], "%Y-%m-%d %H:%M:%S")

    adjusted_order_time = order_datetime - timedelta(hours=int(sender_city.utc_offset))

    order_search = OrderSearchORM(
        material_id=data.get("material_id"),
        search_type="REGION",
        filters={
            "recipient_city": recipient_city.name,
            "recipient_region": recipient_city.region,
            "sender_city": sender_city.name,
            "sender_region": sender_city.region,
            "country": country.name,
            "order_datetime": str(adjusted_order_time),
            "photo_id": data["photo_id"],
        },
    )

    uow.session.add(order_search)
    await uow.session.commit()
    await state.clear()

    await bot.edit_message_reply_markup(
        inline_message_id=call.inline_message_id, reply_markup=None
    )

    await call.bot.send_message(
        chat_id=call.from_user.id,
        text=(
            f"✅ Ваш заказ принят в обработку!\n"
            f"🔍 Мы начали поиск, это может занять некоторое время.\n"
            f"🆔 Идентификатор поиска: #{order_search.id}\n"
            f"⏱ Максимальное время ожидания — 2 часа.\n"
            f"Спасибо за терпение! 🚀"
        ),
    )
