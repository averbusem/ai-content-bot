from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    back_to_menu_keyboard,
    main_menu_keyboard,
    post_schedule_confirm_keyboard,
    post_schedule_remind_offset_keyboard,
)
from src.bot.states import MainMenuStates, PostScheduleStates
from src.schemas.posts import PostContentSchema, PostScheduleInputSchema
from src.services.post_schedule import PostScheduleService


router = Router()


DEFAULT_REMIND_OFFSET_MINUTES = 30


def _format_datetime_moscow(dt_utc: datetime) -> str:
    """
    Преобразует UTC datetime в строку по Мск в человекочитаемом формате.
    """
    moscow_dt = dt_utc.astimezone(timezone(timedelta(hours=3)))
    return moscow_dt.strftime("%d.%m.%Y %H:%M")


@router.callback_query(F.data == "post_schedule:set_reminder")
async def set_reminder_mode(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Выбор режима: только напоминание (без автопубликации).
    """
    await state.update_data(auto_publish=False)
    await state.set_state(PostScheduleStates.publish_at_input)
    await callback.answer()
    await callback.message.edit_text(
        "⏰ <b>Настройка напоминания</b>\n\n"
        "Укажите дату и время публикации по Мск в формате:\n"
        "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
        "Например: <code>25.12.2025 10:30</code>.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "post_schedule:set_autopost")
async def set_autopost_mode(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Выбор режима: напоминание + автопубликация.
    """
    await state.update_data(auto_publish=True)
    await state.set_state(PostScheduleStates.publish_at_input)
    await callback.answer()
    await callback.message.edit_text(
        "📆 <b>Автопубликация поста</b>\n\n"
        "Укажите дату и время публикации по Мск в формате:\n"
        "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
        "Например: <code>25.12.2025 10:30</code>.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(PostScheduleStates.publish_at_input, F.text)
async def publish_at_input_handler(message: types.Message, state: FSMContext) -> None:
    """
    Принимает от пользователя локальное время публикации (строкой).
    """
    publish_at_local = message.text.strip()

    if not publish_at_local:
        await message.answer(
            "Пожалуйста, укажите дату и время в формате <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await state.update_data(publish_at_local=publish_at_local)
    await state.set_state(PostScheduleStates.remind_offset_selection)

    await message.answer(
        "⏱ <b>За сколько времени до публикации напомнить?</b>\n\n"
        "Выберите интервал, за который бот отправит напоминание перед запланированной публикацией поста.",
        reply_markup=post_schedule_remind_offset_keyboard(),
    )


@router.message(PostScheduleStates.publish_at_input)
async def publish_at_invalid_handler(
    message: types.Message,
    state: FSMContext,
) -> None:
    """
    Обработка некорректного формата времени (например, не текстовое сообщение).
    """
    await message.answer(
        "Пожалуйста, отправьте время в текстовом формате, например:\n"
        "<code>25.12.2025 10:30</code>.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("post_schedule:remind_offset:"))
async def remind_offset_selection_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработка выбора интервала напоминания перед публикацией.
    """
    # Ожидаем строку вида "post_schedule:remind_offset:15"
    try:
        _, _, offset_str = callback.data.split(":")
        remind_offset_minutes = int(offset_str)
    except Exception:
        await callback.answer(
            "Не удалось определить интервал напоминания.", show_alert=True
        )
        return

    await state.update_data(remind_offset_minutes=remind_offset_minutes)
    await state.set_state(PostScheduleStates.content_input)

    await callback.answer()
    await callback.message.edit_text(
        "📝 <b>Контент поста</b>\n\n"
        "Пришлите текст поста. Можно прикрепить картинку с подписью — тогда в посте будет использована эта картинка и подпись.\n\n"
        "Важно: сейчас пост ещё не сохраняется в БД, вы сможете подтвердить настройки на следующем шаге.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(PostScheduleStates.content_input, F.photo)
async def content_with_photo_handler(message: types.Message, state: FSMContext) -> None:
    """
    Принимает пост с картинкой: используем caption как текст и file_id фото.
    """
    caption = (message.caption or "").strip()
    if not caption:
        await message.answer(
            "Для запланированного поста нужен текст.\n"
            "Пожалуйста, отправьте фото с подписью (caption) или отдельным текстовым сообщением.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    if not message.photo:
        await message.answer(
            "Не удалось получить файл изображения. Попробуйте отправить картинку ещё раз.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    photo = message.photo[-1]
    await state.update_data(
        content_text=caption,
        photo_file_id=photo.file_id,
    )
    await state.set_state(PostScheduleStates.confirmation)

    data = await state.get_data()
    mode_text = (
        "⏰ Напоминание без автопубликации"
        if not data.get("auto_publish")
        else "📆 Напоминание + автопубликация"
    )

    await message.answer(
        "✅ <b>Проверьте настройки запланированного поста</b>\n\n"
        f"<b>Режим:</b> {mode_text}\n"
        f"<b>Время публикации (по Мск):</b> {data.get('publish_at_local')}\n\n"
        "<b>Текст поста:</b>\n"
        f"{caption}",
        reply_markup=post_schedule_confirm_keyboard(),
    )


@router.message(PostScheduleStates.content_input, F.text)
async def content_text_handler(message: types.Message, state: FSMContext) -> None:
    """
    Принимает текстовый пост без картинки.
    """
    text = message.text.strip()
    if not text:
        await message.answer(
            "Пожалуйста, отправьте непустой текст поста.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await state.update_data(
        content_text=text,
        photo_file_id=None,
    )
    await state.set_state(PostScheduleStates.confirmation)

    data = await state.get_data()
    mode_text = (
        "⏰ Напоминание без автопубликации"
        if not data.get("auto_publish")
        else "📆 Напоминание + автопубликация"
    )

    await message.answer(
        "✅ <b>Проверьте настройки запланированного поста</b>\n\n"
        f"<b>Режим:</b> {mode_text}\n"
        f"<b>Время публикации (по Мск):</b> {data.get('publish_at_local')}\n\n"
        "<b>Текст поста:</b>\n"
        f"{text}",
        reply_markup=post_schedule_confirm_keyboard(),
    )


@router.message(PostScheduleStates.content_input)
async def content_invalid_handler(
    message: types.Message,
    state: FSMContext,
) -> None:
    """
    Обработка неподдерживаемых типов сообщений на шаге ввода контента.
    """
    await message.answer(
        "Пожалуйста, отправьте текстовое сообщение или фото с подписью для запланированного поста.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "post_schedule:cancel")
async def post_schedule_cancel(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Отмена флоу планирования поста, возврат в главное меню.
    """
    await state.clear()
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Планирование поста отменено.")
    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите действие из списка ниже:",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "post_schedule:confirm")
async def post_schedule_confirm(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """
    Финальное подтверждение: создаём запланированный пост через PostScheduleService.
    """
    data = await state.get_data()

    publish_at_local = data.get("publish_at_local")
    auto_publish = bool(data.get("auto_publish"))
    content_text = data.get("content_text")
    photo_file_id = data.get("photo_file_id")

    if not publish_at_local or not content_text:
        await callback.answer()
        await callback.message.edit_text(
            "❌ Не удалось собрать данные для планирования поста. "
            "Попробуйте начать заново.",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        await state.set_state(MainMenuStates.main_menu)
        return

    from_user = callback.from_user
    message_chat = callback.message.chat if callback.message else None
    if not from_user or not message_chat:
        await callback.answer()
        await callback.message.edit_text(
            "❌ Не удалось определить пользователя или чат для планирования поста.",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        await state.set_state(MainMenuStates.main_menu)
        return

    user_id = from_user.id
    chat_id = message_chat.id

    content = PostContentSchema(
        text=content_text,
        photo_file_id=photo_file_id,
    )

    # Если пользователь не выбрал интервал (на всякий случай), используем значение по умолчанию
    remind_offset_minutes = int(
        data.get("remind_offset_minutes") or DEFAULT_REMIND_OFFSET_MINUTES
    )
    schedule_input = PostScheduleInputSchema(
        publish_at=publish_at_local,
        remind_offset_minutes=remind_offset_minutes,
        auto_publish=auto_publish,
    )

    service = PostScheduleService(session=session)

    await callback.answer("Сохраняю запланированный пост...")

    try:
        scheduled_post = await service.schedule_post(
            user_id=user_id,
            chat_id=chat_id,
            content=content,
            schedule_input=schedule_input,
        )
    except ValueError as e:
        # Ошибка валидации времени или входных данных
        await callback.message.edit_text(
            "❌ Ошибка в параметрах расписания:\n"
            f"{e}\n\n"
            "Пожалуйста, укажите дату и время ещё раз в формате:\n"
            "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>.",
            reply_markup=back_to_menu_keyboard(),
        )
        await state.set_state(PostScheduleStates.publish_at_input)
        return
    except Exception:
        await callback.message.edit_text(
            "❌ Произошла ошибка при сохранении запланированного поста. "
            "Попробуйте ещё раз позже.",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        await state.set_state(MainMenuStates.main_menu)
        return

    await state.clear()
    await state.set_state(MainMenuStates.main_menu)

    moscow_publish_at = _format_datetime_moscow(scheduled_post.publish_at)

    mode_text = (
        "⏰ Напоминание без автопубликации"
        if not scheduled_post.auto_publish
        else "📆 Напоминание + автопубликация"
    )

    await callback.message.edit_text(
        "✅ <b>Пост успешно запланирован!</b>\n\n"
        f"<b>Режим:</b> {mode_text}\n"
        f"<b>Публикация по Мск:</b> {moscow_publish_at}\n"
        f"<b>Напоминание за:</b> {scheduled_post.remind_offset_minutes} мин. до публикации\n\n"
        "Вернитесь в главное меню, чтобы запланировать ещё один пост или воспользоваться другими функциями бота.",
        reply_markup=main_menu_keyboard(),
    )
