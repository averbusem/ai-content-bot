from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import back_to_menu_keyboard, text_generation_results_keyboard, main_menu_keyboard, \
    text_redactor_results_keyboard
from src.bot.states import TextEditorStates, MainMenuStates
from src.services.ai_manager import AIManager

router = Router()
ai_manager = AIManager()


@router.message(TextEditorStates.post_input, F.text)
async def post_input_handler(message: types.Message, state: FSMContext):
    user_text = message.text.strip()

    if not user_text:
        return await message.answer(
            "Пожалуйста, отправьте текст.",
            reply_markup=back_to_menu_keyboard()
        )

    await state.set_state(TextEditorStates.edit_input)
    await state.update_data(user_text=user_text)

    return await message.answer(
        f"Пришлите идеи по улучшению текста",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(TextEditorStates.edit_input, F.text)
async def edit_input_handler(message: types.Message, state: FSMContext):
    edit_text = message.text.strip()

    if not edit_text:
        return await message.answer(
            "Пожалуйста, отправьте текст.",
            reply_markup=back_to_menu_keyboard()
        )

    user_id = message.from_user.id

    await state.set_state(TextEditorStates.waiting_results)
    await state.update_data(edit_text=edit_text)
    state_data = await state.get_data()

    loading_msg = await message.answer("⏳ Создаю пост...")

    try:
        post = await ai_manager.edit_post(
            user_id=user_id,
            original_post=state_data['user_text'],
            edit_request=edit_text
        )
    except Exception as e:
        await loading_msg.delete()
        return await message.answer(
            f"❌ Произошла ошибка при создании поста: {str(e)}",
            reply_markup=back_to_menu_keyboard()
        )

    await loading_msg.delete()

    await state.update_data(post=post)
    await message.answer(
        "✨ <b>Готово! Ваш пост:</b>"
    )
    await message.answer(
        f"{post}"
    )
    return await message.answer(
        f"Выберите действие",
        reply_markup=text_redactor_results_keyboard()
    )


@router.message(TextEditorStates.post_input)
async def free_text_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "text_editor:ok")
async def text_result_ok_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Рад был помочь! 🎉")
    return await callback.message.edit_text(
        "👋 Главное меню",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "text_editor:edit")
async def text_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextEditorStates.editing)
    await callback.answer()
    return await callback.message.edit_text(
        "✏️ <b>Редактирование поста</b>\n\n"
        "Что нужно изменить в посте? Опишите ваши пожелания.",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(TextEditorStates.editing, F.text)
async def editing_handler(message: types.Message, state: FSMContext):
    edit_request = message.text.strip()

    if not edit_request:
        return await message.answer(
            "Пожалуйста, опишите, что нужно изменить.",
            reply_markup=back_to_menu_keyboard()
        )

    data = await state.get_data()
    original_post = data.get("user_text", "")

    if not original_post:
        return await message.answer(
            "❌ Не найден исходный пост для редактирования.",
            reply_markup=back_to_menu_keyboard()
        )

    user_id = message.from_user.id

    loading_msg = await message.answer("⏳ Обновляю пост...")

    try:
        # Используем edit_post для редактирования на основе исходного поста
        updated_post = await ai_manager.edit_post(
            user_id=user_id,
            original_post=original_post,
            edit_request=edit_request
        )
    except Exception as e:
        await loading_msg.delete()
        return await message.answer(
            f"❌ Произошла ошибка при обновлении поста: {str(e)}",
            reply_markup=back_to_menu_keyboard()
        )

    await loading_msg.delete()

    await state.update_data(post=updated_post)
    await state.set_state(TextEditorStates.waiting_results)

    await message.answer(
        "✨ <b>Пост обновлён:</b>"
    )
    await message.answer(
        f"{updated_post}"
    )
    return await message.answer(
        "Выберите действие",
        reply_markup=text_generation_results_keyboard()
    )


@router.message(TextEditorStates.editing)
async def editing_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием изменений.",
        reply_markup=back_to_menu_keyboard()
    )
