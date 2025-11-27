from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    back_to_menu_keyboard,
    text_redactor_results_keyboard,
)
from src.bot.states import TextEditorStates
from src.services.ai_manager import ai_manager
from src.bot.bot_decorators import check_user_limit, track_user_operation
from src.bot.handlers.utils.text_formatter import markdown_to_html

router = Router()


@router.message(TextEditorStates.original_text, F.text)
async def original_text_handler(message: types.Message, state: FSMContext):
    original_text = message.text.strip()
    await state.set_state(TextEditorStates.edit_request)
    await state.update_data(original_text=original_text)

    return await message.answer(
        "Пришлите идеи по улучшению текста", reply_markup=back_to_menu_keyboard()
    )


# Если пользователь отправил НЕ текст
@router.message(TextEditorStates.original_text)
async def text_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextEditorStates.edit_request, F.text)
async def edit_request_handler(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    edit_text = message.text.strip()
    user_id = message.from_user.id

    await state.set_state(TextEditorStates.waiting_results)
    await state.update_data(edit_text=edit_text)
    state_data = await state.get_data()

    loading_msg = await message.answer("⏳ Редактирую текст...")

    try:
        edited_text, errors, recommendations = await ai_manager.edit_post(
            user_id=user_id,
            session=session,
            original_post=state_data["original_text"],
            edit_request=edit_text,
        )
    except Exception:
        await loading_msg.delete()
        return await message.answer(
            "❌ Произошла ошибка при создании поста. Попробуйте ещё раз позже",
            reply_markup=back_to_menu_keyboard(),
        )

    await loading_msg.delete()

    # Проверяем, что edited_text не пустой
    if not edited_text or not edited_text.strip():
        return await message.answer(
            "❌ Не удалось получить исправленный текст. Попробуйте еще раз.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(post=edited_text)

    # Отправляем исправленный текст
    await message.answer("✨ <b>Исправленный текст:</b>")
    await message.answer(markdown_to_html(edited_text))

    await track_user_operation(user_id)

    # Формируем и отправляем аналитику
    analytics_parts = []

    if errors:
        errors_text = "🔍 <b>Найденные ошибки:</b>\n"
        for error in errors:
            errors_text += f"{error}\n"
        analytics_parts.append(errors_text)

    if recommendations:
        recs_text = "💡 <b>Рекомендации по улучшению:</b>\n"
        for rec in recommendations:
            recs_text += f"{rec}\n"
        analytics_parts.append(recs_text)

    if analytics_parts:
        await message.answer("\n".join(analytics_parts))

    return await message.answer(
        "Выберите действие", reply_markup=text_redactor_results_keyboard()
    )


@router.callback_query(F.data == "text_editor:edit")
@check_user_limit()
async def text_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextEditorStates.editing)
    await callback.answer()
    return await callback.message.edit_text(
        "✏️ <b>Редактирование поста</b>\n\n"
        "Что нужно изменить в посте? Опишите ваши пожелания.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextEditorStates.editing, F.text)
async def editing_handler(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    edit_text = message.text.strip()
    data = await state.get_data()
    original_post = data.get("post", "")
    if not original_post:
        return await message.answer(
            "❌ Не найден исходный пост для редактирования.",
            reply_markup=back_to_menu_keyboard(),
        )

    user_id = message.from_user.id

    loading_msg = await message.answer("⏳ Редактирую текст...")

    try:
        # Используем edit_post для редактирования на основе исходного поста
        edited_text, errors, recommendations = await ai_manager.edit_post(
            user_id=user_id,
            session=session,
            original_post=original_post,
            edit_request=edit_text,
        )
    except Exception:
        await loading_msg.delete()
        return await message.answer(
            "❌ Произошла ошибка при обновлении поста. Попробуйте ещё раз позже",
            reply_markup=back_to_menu_keyboard(),
        )

    await loading_msg.delete()

    # Проверяем, что edited_text не пустой
    if not edited_text or not edited_text.strip():
        return await message.answer(
            "❌ Не удалось получить исправленный текст. Попробуйте еще раз.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(post=edited_text)

    await message.answer("✨ <b>Исправленный текст:</b>")
    await message.answer(markdown_to_html(edited_text))

    await track_user_operation(user_id)

    # Формируем и отправляем аналитику
    analytics_parts = []

    if errors:
        errors_text = "🔍 <b>Найденные ошибки:</b>\n"
        for error in errors:
            errors_text += f"{error}\n"
        analytics_parts.append(errors_text)

    if recommendations:
        recs_text = "💡 <b>Рекомендации по улучшению:</b>\n"
        for rec in recommendations:
            recs_text += f"{rec}\n"
        analytics_parts.append(recs_text)

    if analytics_parts:
        await message.answer("\n".join(analytics_parts))

    return await message.answer(
        "Выберите действие", reply_markup=text_redactor_results_keyboard()
    )


# Если пользователь отправил НЕ текст
@router.message(TextEditorStates.editing)
async def editing_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием изменений.",
        reply_markup=back_to_menu_keyboard(),
    )
