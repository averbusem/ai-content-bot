from contextlib import suppress

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.bot_decorators import track_user_operation
from src.bot.keyboards import (
    back_to_menu_keyboard,
    main_menu_keyboard,
    text_generation_results_keyboard,
)
from src.bot.states import ContentPlanStates, TextGenerationStates
from src.bot.handlers.utils.text_formatter import markdown_to_html
from src.services.ai_manager import ai_manager
from src.services.content_plan_service import ContentPlanService
from src.services.service_decorators import TextLengthLimitError
from src.utils.telegram_html import sanitize_telegram_html

router = Router()


async def _safe_delete_message(message: types.Message | None) -> None:
    """Удаляет сообщение, игнорируя ошибки телеграма."""
    if message is None:
        return
    with suppress(TelegramBadRequest):
        await message.delete()


@router.message(ContentPlanStates.duration_input, F.text)
async def duration_input_handler(message: types.Message, state: FSMContext):
    duration_text = message.text.strip()

    try:
        duration_days = int(duration_text)

        if duration_days < 1:
            return await message.answer(
                "❌ Количество дней должно быть больше 0.\nПопробуйте ещё раз:",
                reply_markup=back_to_menu_keyboard(),
            )

        if duration_days > 90:
            return await message.answer(
                "❌ Максимальный период - 90 дней.\nПопробуйте указать меньше:",
                reply_markup=back_to_menu_keyboard(),
            )

        await state.update_data(duration_days=duration_days)
        await state.set_state(ContentPlanStates.frequency_input)

        return await message.answer(
            f"✅ Период: {duration_days} дней\n\n"
            "Сколько постов в неделю планируете публиковать?\n"
            "Укажите число от 1 до 14 (например: 3, 5, 7)",
            reply_markup=back_to_menu_keyboard(),
        )

    except ValueError:
        return await message.answer(
            "❌ Пожалуйста, введите число (количество дней).\nНапример: 7, 14 или 30",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(ContentPlanStates.duration_input)
async def duration_invalid_handler(message: types.Message):
    return await message.answer(
        "❌ Пожалуйста, отправьте число (количество дней).\nНапример: 7, 14 или 30",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ContentPlanStates.frequency_input, F.text)
async def frequency_input_handler(message: types.Message, state: FSMContext):
    frequency_text = message.text.strip()

    try:
        posts_per_week = int(frequency_text)

        if posts_per_week < 1:
            return await message.answer(
                "❌ Количество постов должно быть больше 0.\nПопробуйте ещё раз:",
                reply_markup=back_to_menu_keyboard(),
            )

        if posts_per_week > 14:
            return await message.answer(
                "❌ Максимум 14 постов в неделю.\nПопробуйте указать меньше:",
                reply_markup=back_to_menu_keyboard(),
            )

        await state.update_data(posts_per_week=posts_per_week)
        await state.set_state(ContentPlanStates.preferences_input)

        return await message.answer(
            f"✅ Частота: {posts_per_week} постов в неделю\n\n"
            "Есть ли у вас предпочтения по темам или форматам?\n\n"
            "<i>Примеры:</i>\n"
            "• Контент для студентов и молодых специалистов\n"
            "• Программы стажировок, конкурсы, гранты\n"
            "• STEM-образование и популяризация науки\n"
            "• Истории успеха выпускников наших программ\n"
            "• Вовлекающий формат - вопросы, обсуждения, развенчание стереотипов о работе в атомной отрасли\n\n"
            'Или отправьте <b>"Нет"</b>, чтобы создать сбалансированный план.',
            reply_markup=back_to_menu_keyboard(),
        )

    except ValueError:
        return await message.answer(
            "❌ Пожалуйста, введите число (количество постов).\nНапример: 3, 5 или 7",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(ContentPlanStates.frequency_input)
async def frequency_invalid_handler(message: types.Message):
    return await message.answer(
        "❌ Пожалуйста, отправьте число (количество постов в неделю).\n"
        "Например: 3, 5 или 7",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ContentPlanStates.preferences_input, F.text)
async def preferences_input_handler(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    preferences_text = message.text.strip()

    preferences = (
        None
        if preferences_text.lower() in ["нет", "не нужно", "без предпочтений"]
        else preferences_text
    )

    await state.update_data(preferences=preferences)
    await state.set_state(ContentPlanStates.waiting_results)

    data = await state.get_data()
    duration_days = data.get("duration_days")
    posts_per_week = data.get("posts_per_week")
    user_id = message.from_user.id

    loading_msg = await message.answer("⏳ Создаю контент-план...\n")

    try:
        plan = await ai_manager.generate_content_plan(
            user_id=user_id,
            session=session,
            duration_days=duration_days,
            posts_per_week=posts_per_week,
            preferences=preferences,
        )

        await _safe_delete_message(loading_msg)

        await state.update_data(content_plan=plan)

        try:
            content_plan_service = ContentPlanService(session=session)
            await content_plan_service.save_content_plan(
                user_id=user_id,
                content=plan,
                duration_days=duration_days,
                posts_per_week=posts_per_week,
                preferences=preferences,
            )
        except Exception as e:
            print(f"Ошибка при сохранении контент-плана: {e}")

        await message.answer(
            "✨ <b>Ваш контент-план готов!</b>\n\n"
            f"📅 Период: {duration_days} дней\n"
            f"📊 Частота: {posts_per_week} постов в неделю\n"
            + (f"💡 Предпочтения: {preferences}\n" if preferences else "")
        )

        safe_plan = sanitize_telegram_html(plan)
        await message.answer(f"<b>📋 КОНТЕНТ-ПЛАН:</b>\n\n{safe_plan}")

        await state.clear()

        await track_user_operation(user_id)
        return await message.answer(
            "✅ Контент-план создан и сохранён!\n\nВы можете посмотреть его в разделе 'Посмотреть контент планы'.",
            reply_markup=main_menu_keyboard(),
        )

    except Exception:
        await _safe_delete_message(loading_msg)
        await state.clear()
        return await message.answer(
            "❌ Произошла ошибка при создании контент-плана:\n"
            "Попробуйте ещё раз позже.",
            reply_markup=main_menu_keyboard(),
        )


@router.message(ContentPlanStates.preferences_input)
async def preferences_invalid_handler(message: types.Message):
    return await message.answer(
        'Пожалуйста, опишите ваши предпочтения текстом\nили отправьте <b>"Нет"</b>.',
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "content_plan:list")
async def content_plan_list_handler(
    callback: types.CallbackQuery, session: AsyncSession
):
    """Показать список контент-планов пользователя."""
    user_id = callback.from_user.id
    content_plan_service = ContentPlanService(session=session)

    plans, total = await content_plan_service.get_user_plans(
        user_id=user_id, page=1, per_page=5
    )

    if not plans:
        await callback.answer()
        return await callback.message.edit_text(
            "📋 <b>Контент-планы</b>\n\n"
            "У вас пока нет сохранённых контент-планов.\n"
            "Создайте новый контент-план, чтобы он появился здесь.",
            reply_markup=back_to_menu_keyboard(),
        )

    from src.bot.keyboards import content_plans_list_keyboard

    total_pages = (total + 4) // 5
    text = f"📋 <b>Ваши контент-планы</b>\n\nВсего: {total}\n\nВыберите контент-план:"

    await callback.answer()
    return await callback.message.edit_text(
        text,
        reply_markup=content_plans_list_keyboard(plans, 1, total_pages),
    )


@router.callback_query(F.data.startswith("content_plan:list_page:"))
async def content_plan_list_page_handler(
    callback: types.CallbackQuery, session: AsyncSession
):
    """Обработчик пагинации списка контент-планов."""
    page = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    content_plan_service = ContentPlanService(session=session)

    plans, total = await content_plan_service.get_user_plans(
        user_id=user_id, page=page, per_page=5
    )

    if not plans:
        await callback.answer("Нет контент-планов на этой странице", show_alert=True)
        return

    from src.bot.keyboards import content_plans_list_keyboard

    total_pages = (total + 4) // 5
    text = f"📋 <b>Ваши контент-планы</b>\n\nСтраница {page} из {total_pages}\nВсего: {total}"

    await callback.answer()
    return await callback.message.edit_text(
        text,
        reply_markup=content_plans_list_keyboard(plans, page, total_pages),
    )


@router.callback_query(F.data.startswith("content_plan:view:"))
async def content_plan_view_handler(
    callback: types.CallbackQuery, session: AsyncSession
):
    """Показать дни контент-плана."""
    plan_id = int(callback.data.split(":")[-1])
    content_plan_service = ContentPlanService(session=session)

    plan = await content_plan_service.get_plan_by_id(plan_id)
    if not plan:
        await callback.answer("Контент-план не найден", show_alert=True)
        return

    days, total = await content_plan_service.get_plan_days(
        plan_id=plan_id, page=1, per_page=5
    )

    if not days:
        await callback.answer()
        return await callback.message.edit_text(
            f"📋 <b>{plan.name}</b>\n\nВ этом контент-плане пока нет дней.",
            reply_markup=back_to_menu_keyboard(),
        )

    from src.bot.keyboards import content_plan_days_keyboard

    total_pages = (total + 4) // 5
    text = (
        f"📋 <b>{plan.name}</b>\n\n"
        f"📅 Период: {plan.duration_days} дней\n"
        f"📊 Частота: {plan.posts_per_week} постов в неделю\n"
        f"📝 Всего дней: {total}\n\n"
        "Выберите день для просмотра:"
    )

    await callback.answer()
    return await callback.message.edit_text(
        text,
        reply_markup=content_plan_days_keyboard(days, plan_id, 1, total_pages),
    )


@router.callback_query(F.data.startswith("content_plan:delete:"))
async def content_plan_delete_handler(
    callback: types.CallbackQuery, session: AsyncSession
):
    """Удаление контент-плана пользователя."""
    plan_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id

    content_plan_service = ContentPlanService(session=session)

    plan = await content_plan_service.get_plan_by_id(plan_id)
    if not plan or plan.user_id != user_id:
        await callback.answer(
            "Контент-план не найден или вам недоступен", show_alert=True
        )
        return

    deleted = await content_plan_service.delete_content_plan(
        user_id=user_id, plan_id=plan_id
    )
    if not deleted:
        await callback.answer("Не удалось удалить контент-план", show_alert=True)
        return

    # После удаления показываем обновлённый список планов
    plans, total = await content_plan_service.get_user_plans(
        user_id=user_id, page=1, per_page=5
    )

    from src.bot.keyboards import content_plans_list_keyboard

    await callback.answer("Контент-план удалён", show_alert=False)

    if not plans:
        return await callback.message.edit_text(
            "📋 <b>Контент-планы</b>\n\nУ вас больше нет сохранённых контент-планов.",
            reply_markup=back_to_menu_keyboard(),
        )

    total_pages = (total + 4) // 5
    text = f"📋 <b>Ваши контент-планы</b>\n\nВсего: {total}\n\nВыберите контент-план:"

    return await callback.message.edit_text(
        text,
        reply_markup=content_plans_list_keyboard(plans, 1, total_pages),
    )


@router.callback_query(F.data.startswith("content_plan:days_page:"))
async def content_plan_days_page_handler(
    callback: types.CallbackQuery, session: AsyncSession
):
    """Обработчик пагинации дней контент-плана."""
    parts = callback.data.split(":")
    plan_id = int(parts[-2])
    page = int(parts[-1])
    content_plan_service = ContentPlanService(session=session)

    plan = await content_plan_service.get_plan_by_id(plan_id)
    if not plan:
        await callback.answer("Контент-план не найден", show_alert=True)
        return

    days, total = await content_plan_service.get_plan_days(
        plan_id=plan_id, page=page, per_page=5
    )

    if not days:
        await callback.answer("Нет дней на этой странице", show_alert=True)
        return

    from src.bot.keyboards import content_plan_days_keyboard

    total_pages = (total + 4) // 5
    text = (
        f"📋 <b>{plan.name}</b>\n\n"
        f"Страница {page} из {total_pages}\n"
        "Выберите день для просмотра:"
    )

    await callback.answer()
    return await callback.message.edit_text(
        text,
        reply_markup=content_plan_days_keyboard(days, plan_id, page, total_pages),
    )


@router.callback_query(F.data.startswith("content_plan:day:"))
async def content_plan_day_handler(
    callback: types.CallbackQuery, session: AsyncSession
):
    """Показать детали дня контент-плана."""
    day_id = int(callback.data.split(":")[-1])
    content_plan_service = ContentPlanService(session=session)

    day = await content_plan_service.get_day_by_id(day_id)
    if not day:
        await callback.answer("День не найден", show_alert=True)
        return

    plan = await content_plan_service.get_plan_by_id(day.content_plan_id)
    if not plan:
        await callback.answer("Контент-план не найден", show_alert=True)
        return

    from src.bot.keyboards import content_plan_day_detail_keyboard

    text = (
        f"📅 <b>День контент-плана</b>\n\n"
        f"📆 Дата: {day.day_name} {day.date}, {day.time}\n"
        f"📋 Неделя: {day.week}\n"
    )

    if day.post_type:
        text += f"📝 Тип: {day.post_type}\n"
    if day.topic:
        text += f"💡 Тема: {day.topic}\n"
    if day.format:
        text += f"🎨 Формат: {day.format}\n"

    await callback.answer()
    return await callback.message.edit_text(
        text,
        reply_markup=content_plan_day_detail_keyboard(day_id, day.content_plan_id),
    )


@router.callback_query(F.data.startswith("content_plan:generate_post:"))
async def content_plan_generate_post_handler(
    callback: types.CallbackQuery, session: AsyncSession, state: FSMContext
):
    """Обработчик генерации поста для дня контент-плана."""
    day_id = int(callback.data.split(":")[-1])
    content_plan_service = ContentPlanService(session=session)

    day = await content_plan_service.get_day_by_id(day_id)
    if not day:
        await callback.answer("День не найден", show_alert=True)
        return

    user_id = callback.from_user.id
    await callback.answer()

    if day.topic:
        user_idea = f"Создай пост на тему: {day.topic}"
        if day.post_type:
            user_idea += f"\nТип поста: {day.post_type}"
        if day.format:
            user_idea += f"\nФормат: {day.format}"
    else:
        user_idea = "Создай пост для социальных сетей"

    loading_msg = await callback.message.answer("⏳ Создаю пост...")

    try:
        post = await ai_manager.generate_free_text_post(
            user_id=user_id,
            session=session,
            user_idea=user_idea,
            style="разговорный",
        )

        await loading_msg.edit_text("⏳ Создаю изображение для поста...")

        image_bytes = await ai_manager.generate_image_from_post(post_text=post)

        await _safe_delete_message(loading_msg)

        await callback.message.answer("✨ <b>Готово! Ваш пост:</b>")

        image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
        photo_message = await callback.message.answer_photo(
            photo=image_file, caption=markdown_to_html(post)
        )

        image_file_id = photo_message.photo[-1].file_id if photo_message.photo else None

        await state.set_state(TextGenerationStates.waiting_results)
        await state.update_data(
            post=post,
            has_image=True,
            image_file_id=image_file_id,
            content_plan_day_id=day_id,
        )

        await track_user_operation(user_id)

        return await callback.message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except TextLengthLimitError:
        await _safe_delete_message(loading_msg)
        return await callback.message.answer(
            "❌ Не удалось получить текст подходящей длины (до 1024 символов).\n"
            "Попробуйте ещё раз позже.",
            reply_markup=back_to_menu_keyboard(),
        )

    except Exception:
        await _safe_delete_message(loading_msg)
        return await callback.message.answer(
            "❌ Произошла ошибка при генерации поста.\nПопробуйте ещё раз позже.",
            reply_markup=back_to_menu_keyboard(),
        )
