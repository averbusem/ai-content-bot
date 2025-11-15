from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import back_to_menu_keyboard, text_generation_results_keyboard, main_menu_keyboard
from src.bot.states import TextGenerationStates, MainMenuStates
from src.services.ai_manager import AIManager

router = Router()
ai_manager = AIManager()


@router.callback_query(F.data == "text_gen:free_text")
async def free_text_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStates.free_text_input)
    await callback.answer()
    return await callback.message.edit_text(
        "💬 <b>Свободный текст</b>\n\n"
        "Опишите, какой пост вы хотите создать. Вы можете:\n"
        "• Написать текст\n"
        "• Отправить голосовое сообщение\n\n"
        "<i>Примеры запросов:</i>\n"
        "• \"Создай пост о нашем благотворительном концерте\"\n"
        "• \"Нужен пост для привлечения волонтёров\"\n"
        "• \"Расскажи о нашей новой программе помощи\"",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(TextGenerationStates.free_text_input, F.text)
async def free_text_input_handler(message: types.Message, state: FSMContext):
    user_text = message.text.strip()
    
    if not user_text:
        return await message.answer(
            "Пожалуйста, отправьте текст или голосовое сообщение.",
            reply_markup=back_to_menu_keyboard()
        )
    
    user_id = message.from_user.id
    
    await state.set_state(TextGenerationStates.waiting_results)
    await state.update_data(user_text=user_text)
    
    loading_msg = await message.answer("⏳ Генерирую пост...")
    
    try:
        post = await ai_manager.generate_free_text_post(
            user_id=user_id,
            user_idea=user_text
        )
    except Exception as e:
        await loading_msg.delete()
        return await message.answer(
            f"❌ Произошла ошибка при генерации поста: {str(e)}",
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
        reply_markup=text_generation_results_keyboard()
    )


@router.message(TextGenerationStates.free_text_input, F.voice)
async def free_text_voice_handler(message: types.Message, state: FSMContext):
    if message.voice and hasattr(message.voice, 'file_id'):
        if message.caption:
            user_text = message.caption.strip()
        else:
            return await message.answer(
                "Голосовые сообщения пока поддерживаются только с текстовым описанием. "
                "Пожалуйста, отправьте текст или добавьте описание к голосовому сообщению.",
                reply_markup=back_to_menu_keyboard()
            )
    else:
        return await message.answer(
            "Пожалуйста, отправьте текстовое сообщение.",
            reply_markup=back_to_menu_keyboard()
        )
    
    user_id = message.from_user.id
    
    await state.set_state(TextGenerationStates.waiting_results)
    await state.update_data(user_text=user_text)
    
    loading_msg = await message.answer("⏳ Генерирую пост...")
    
    try:
        post = await ai_manager.generate_free_text_post(
            user_id=user_id,
            user_idea=user_text
        )
    except Exception as e:
        await loading_msg.delete()
        return await message.answer(
            f"❌ Произошла ошибка при генерации поста: {str(e)}",
            reply_markup=back_to_menu_keyboard()
        )
    
    await loading_msg.delete()
    
    await state.update_data(post=post)
    
    return await message.answer(
        "✨ <b>Готово! Ваш пост:</b>\n\n"
        f"{post}",
        reply_markup=text_generation_results_keyboard()
    )


@router.message(TextGenerationStates.free_text_input)
async def free_text_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение или голосовое сообщение с описанием.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "text_result:ok")
async def text_result_ok_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Рад был помочь! 🎉")
    return await callback.message.edit_text(
        "👋 Главное меню",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "text_result:edit")
async def text_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStates.editing)
    await callback.answer()
    return await callback.message.edit_text(
        "✏️ <b>Редактирование поста</b>\n\n"
        "Что нужно изменить в посте? Опишите ваши пожелания.",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(TextGenerationStates.editing, F.text)
async def editing_handler(message: types.Message, state: FSMContext):
    edit_request = message.text.strip()
    
    if not edit_request:
        return await message.answer(
            "Пожалуйста, опишите, что нужно изменить.",
            reply_markup=back_to_menu_keyboard()
        )
    
    data = await state.get_data()
    original_post = data.get("post", "")
    user_text = data.get("user_text", "")
    
    # Объединяем исходный запрос с уточнением
    combined_request = f"{user_text}\n\nДополнительно: {edit_request}"
    
    user_id = message.from_user.id
    
    loading_msg = await message.answer("⏳ Обновляю пост...")
    
    try:
        # Используем edit_text для редактирования
        edit_result = await ai_manager.edit_text(
            text=original_post,
            edit_focus=edit_request
        )
        updated_post = edit_result.get("edited_text", original_post)
    except Exception as e:
        # Если редактирование не сработало, генерируем заново
        try:
            updated_post = await ai_manager.generate_free_text_post(
                user_id=user_id,
                user_idea=combined_request
            )
        except Exception as e2:
            await loading_msg.delete()
            return await message.answer(
                f"❌ Произошла ошибка при обновлении поста: {str(e2)}",
                reply_markup=back_to_menu_keyboard()
            )
    
    await loading_msg.delete()
    
    await state.update_data(post=updated_post)
    await state.set_state(TextGenerationStates.waiting_results)

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


@router.message(TextGenerationStates.editing)
async def editing_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием изменений.",
        reply_markup=back_to_menu_keyboard()
    )
