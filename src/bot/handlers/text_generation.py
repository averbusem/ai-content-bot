from typing import Optional

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.bot_decorators import check_user_limit, track_user_operation
from src.bot.keyboards import (
    back_to_menu_keyboard,
    text_generation_results_keyboard,
    main_menu_keyboard,
    image_attachment_type_keyboard,
    image_attachment_position_keyboard,
)
from src.bot.states import TextGenerationStates, MainMenuStates
from src.services.ai_manager import ai_manager
from src.bot.handlers.utils.image_overlay import build_image_with_overlay
from src.services.service_decorators import TextLengthLimitError

router = Router()


def _extract_image_file_id(message: types.Message) -> Optional[str]:
    """Возвращает file_id изображения из сообщения пользователя."""
    if message.photo:
        return message.photo[-1].file_id

    if message.document:
        mime_type = message.document.mime_type or ""
        if mime_type.startswith("image/"):
            return message.document.file_id

    return None


@router.callback_query(F.data == "text_gen:free_text")
@check_user_limit()
async def free_text_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStates.free_text_input)
    await callback.answer()
    return await callback.message.edit_text(
        "💬 <b>Свободный текст</b>\n\n"
        "Опишите, какой пост вы хотите создать. Вы можете:\n"
        "• Написать текст\n"
        "• Отправить голосовое сообщение\n\n"
        "<i>💡 Чем подробнее описание, тем лучше результат!</i>\n\n"
        "<i>Пример хорошего запроса:</i>\n"
        "\"Создай пост о том, что мы провели IT-хакатон 'Энергия добра'. "
        "Он проходил в онлайн формате, в нём участвовали более 300 человек.\n"
        "Было 3 кейса:\n"
        "Телеграм-бот для создания ИИ контента (постов)\n"
        "Онлайн-навигатор по социальным проектам и НКО в городах присутствия Росатома"
        "в виде одностраничного сайта \n"
        'Информационный портал для НКО городов Росатома с интерактивной картой."',
        reply_markup=back_to_menu_keyboard(),
    )


async def generate_post_with_image(
    message: types.Message,
    state: FSMContext,
    user_id: int,
    session: AsyncSession,
    user_text: str,
):
    loading_msg = await message.answer("⏳ Создаю пост...")

    try:
        post = await ai_manager.generate_free_text_post(
            user_id=user_id,
            session=session,
            user_idea=user_text,
            style="разговорный",
        )

        await loading_msg.edit_text("⏳ Создаю изображение для поста...")

        image_bytes = await ai_manager.generate_image_from_post(post_text=post)

        await loading_msg.delete()

        await message.answer("✨ <b>Готово! Ваш пост:</b>")

        image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
        photo_message = await message.answer_photo(photo=image_file, caption=post)

        image_file_id = photo_message.photo[-1].file_id if photo_message.photo else None
        await state.update_data(
            post=post,
            has_image=True,
            image_file_id=image_file_id,
        )

        await track_user_operation(user_id)

        return await message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except TextLengthLimitError:
        await loading_msg.delete()
        await state.set_state(TextGenerationStates.free_text_input)
        return await message.answer(
            "❌ Не удалось получить текст подходящей длины (до 1024 символов).\n"
            "Попробуйте описать желаемый пост иначе.",
            reply_markup=back_to_menu_keyboard(),
        )

    except Exception:
        await loading_msg.delete()
        return await message.answer(
            "❌ Произошла ошибка. Попробуйте ещё раз позже",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(TextGenerationStates.free_text_input, F.text)
async def free_text_input_handler(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    user_text = message.text.strip()

    if not user_text:
        return await message.answer(
            "Пожалуйста, отправьте текст или голосовое сообщение.",
            reply_markup=back_to_menu_keyboard(),
        )

    user_id = message.from_user.id
    await state.set_state(TextGenerationStates.waiting_results)
    await state.update_data(user_text=user_text)

    return await generate_post_with_image(
        message=message,
        state=state,
        user_id=user_id,
        session=session,
        user_text=user_text,
    )


@router.message(TextGenerationStates.free_text_input, F.voice)
async def free_text_voice_handler(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    transcribe_msg = await message.answer("⏳ Распознаю речь...")

    try:
        file = await message.bot.get_file(message.voice.file_id)
        audio_file = await message.bot.download_file(file.file_path)
        audio_data = audio_file.read()

        user_text = await ai_manager.transcribe_voice(
            audio_data=audio_data, audio_format="opus"
        )

        await transcribe_msg.delete()

        if not user_text or not user_text.strip():
            return await message.answer(
                "Не удалось распознать речь. Попробуйте отправить голосовое сообщение ещё раз.",
                reply_markup=back_to_menu_keyboard(),
            )

        await message.answer(f"Вы сказали: {user_text}")

        user_id = message.from_user.id
        await state.set_state(TextGenerationStates.waiting_results)
        await state.update_data(user_text=user_text.strip())

        return await generate_post_with_image(
            message=message,
            state=state,
            user_id=user_id,
            session=session,
            user_text=user_text.strip(),
        )

    except Exception:
        await transcribe_msg.delete()
        return await message.answer(
            "❌ Ошибка при распознавании речи. Попробуйте ещё раз позже",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(TextGenerationStates.free_text_input)
async def free_text_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение или голосовое сообщение с описанием.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "text_result:ok")
async def text_result_ok_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Рад был помочь! 🎉")
    return await callback.message.answer(
        "👋 Главное меню", reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "text_result:change_image")
@check_user_limit()
async def text_result_change_image_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    data = await state.get_data()
    post = data.get("post", "")

    if not post:
        await callback.answer("❌ Пост не найден", show_alert=True)
        return

    await callback.answer()
    loading_msg = await callback.message.answer("⏳ Создаю новое изображение...")

    try:
        image_bytes = await ai_manager.generate_image_from_post(post_text=post)

        await loading_msg.delete()

        image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
        photo_message = await callback.message.answer_photo(
            photo=image_file, caption="🖼 Новое изображение для вашего поста"
        )

        image_file_id = photo_message.photo[-1].file_id if photo_message.photo else None
        await state.update_data(image_file_id=image_file_id, has_image=True)

        await track_user_operation(user_id=callback.from_user.id)

        return await callback.message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except Exception:
        await loading_msg.delete()
        await callback.message.answer(
            "❌ Ошибка при создании изображения. Пожалуйста, попробуйте ещё раз позже",
            reply_markup=text_generation_results_keyboard(),
        )


@router.callback_query(
    TextGenerationStates.waiting_results, F.data == "text_result:add_overlay"
)
async def text_result_add_overlay_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    data = await state.get_data()
    image_file_id = data.get("image_file_id")

    if not image_file_id:
        await callback.answer("Сначала сгенерируйте изображение", show_alert=True)
        return

    await state.set_state(TextGenerationStates.adding_overlay)
    await state.update_data(
        pending_overlay_file_id=None,
        pending_overlay_type=None,
    )

    await callback.answer()
    return await callback.message.answer(
        "📎 Пришлите логотип или фотографию, которую нужно добавить на картинку.\n"
        "Можно отправить фото или файл с изображением.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationStates.adding_overlay, F.photo | F.document)
async def adding_overlay_file_handler(message: types.Message, state: FSMContext):
    file_id = _extract_image_file_id(message)

    if not file_id:
        return await message.answer(
            "Пожалуйста, отправьте изображение (фото или файл).",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(pending_overlay_file_id=file_id)
    await state.set_state(TextGenerationStates.adding_overlay_type)
    return await message.answer(
        "Выберите, как использовать изображение:",
        reply_markup=image_attachment_type_keyboard(),
    )


@router.message(TextGenerationStates.adding_overlay)
async def adding_overlay_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте изображение (фото или файл).",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(
    TextGenerationStates.adding_overlay_type,
    F.data.startswith("image_asset:type:"),
)
async def overlay_type_selected_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    _, _, value = callback.data.split(":")

    if value == "cancel":
        await state.set_state(TextGenerationStates.waiting_results)
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await callback.answer("Добавление отменено")
        return await callback.message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    if value not in {"logo", "photo"}:
        await callback.answer("Пожалуйста, используйте кнопки ниже", show_alert=True)
        return

    await state.update_data(pending_overlay_type=value)
    await state.set_state(TextGenerationStates.adding_overlay_position)
    await callback.answer()
    return await callback.message.answer(
        "📍 Где разместить изображение?",
        reply_markup=image_attachment_position_keyboard(),
    )


@router.message(TextGenerationStates.adding_overlay_type)
async def overlay_type_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, выберите вариант с помощью кнопок ниже.",
        reply_markup=image_attachment_type_keyboard(),
    )


@router.callback_query(
    TextGenerationStates.adding_overlay_position,
    F.data.startswith("image_asset:pos:"),
)
async def overlay_position_selected_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    _, _, value = callback.data.split(":")

    if value == "cancel":
        await state.set_state(TextGenerationStates.waiting_results)
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await callback.answer("Добавление отменено")
        return await callback.message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    data = await state.get_data()
    base_image_id = data.get("image_file_id")
    overlay_file_id = data.get("pending_overlay_file_id")
    overlay_type = data.get("pending_overlay_type")

    if not all([base_image_id, overlay_file_id, overlay_type]):
        await state.set_state(TextGenerationStates.waiting_results)
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await callback.answer("Изображение не найдено", show_alert=True)
        return await callback.message.answer(
            "❌ Не удалось подготовить изображение. Попробуйте начать заново.",
            reply_markup=text_generation_results_keyboard(),
        )

    await callback.answer()
    processing_msg = await callback.message.answer("⏳ Добавляю изображение...")

    try:
        merged_bytes = await build_image_with_overlay(
            bot=callback.bot,
            base_file_id=base_image_id,
            overlay_file_id=overlay_file_id,
            overlay_type=overlay_type,
            position=value,
        )
        try:
            await processing_msg.delete()
        except Exception:
            pass

        post_text = data.get("post") or "Обновлённое изображение"
        photo_message = await callback.message.answer_photo(
            photo=BufferedInputFile(
                merged_bytes,
                filename="post_image_with_overlay.png",
            ),
            caption=post_text,
        )

        new_file_id = (
            photo_message.photo[-1].file_id if photo_message.photo else base_image_id
        )

        await state.update_data(
            image_file_id=new_file_id,
            has_image=True,
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await state.set_state(TextGenerationStates.waiting_results)

        await track_user_operation(user_id=callback.from_user.id)

        return await callback.message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except Exception:
        try:
            await processing_msg.delete()
        except Exception:
            pass
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await state.set_state(TextGenerationStates.waiting_results)
        return await callback.message.answer(
            "❌ Не удалось добавить изображение. Попробуйте другой файл.",
            reply_markup=text_generation_results_keyboard(),
        )


@router.message(TextGenerationStates.adding_overlay_position)
async def overlay_position_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, выберите позицию с помощью кнопок.",
        reply_markup=image_attachment_position_keyboard(),
    )


@router.callback_query(F.data == "text_result:edit")
@check_user_limit()
async def text_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStates.editing)
    await callback.answer()
    return await callback.message.answer(
        "✏️ <b>Редактирование поста</b>\n\n"
        "Что нужно изменить в посте? Опишите ваши пожелания.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationStates.editing, F.text)
async def editing_handler(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    edit_request = message.text.strip()
    data = await state.get_data()
    original_post = data.get("post", "")
    image_file_id = data.get("image_file_id")

    if not original_post:
        return await message.answer(
            "❌ Не найден исходный пост для редактирования.",
            reply_markup=back_to_menu_keyboard(),
        )

    user_id = message.from_user.id

    loading_msg = await message.answer("⏳ Обновляю пост...")

    try:
        updated_post = await ai_manager.generate_free_text_post(
            user_id=user_id,
            session=session,
            user_idea=f"Исходный пост:\n{original_post}\n\nИзменения: {edit_request}",
            style="разговорный",
        )

        await loading_msg.edit_text("✨ Сохраняю изменения...")
        await loading_msg.delete()

        await state.update_data(post=updated_post)
        await state.set_state(TextGenerationStates.waiting_results)

        await message.answer("✨ <b>Пост обновлён:</b>")

        if image_file_id:
            photo_message = await message.answer_photo(
                photo=image_file_id, caption=updated_post
            )
            new_image_file_id = (
                photo_message.photo[-1].file_id
                if photo_message.photo
                else image_file_id
            )
            await state.update_data(
                image_file_id=new_image_file_id,
                has_image=True,
            )
        else:
            await message.answer(updated_post)

        await track_user_operation(user_id=user_id)
        return await message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except TextLengthLimitError:
        await loading_msg.delete()
        return await message.answer(
            "❌ Не удалось получить текст подходящей длины (до 1024 символов).\n"
            "Попробуйте переформулировать запрос.",
            reply_markup=back_to_menu_keyboard(),
        )

    except Exception:
        await loading_msg.delete()
        return await message.answer(
            "❌ Произошла ошибка при обновлении поста. Попробуйте ещё раз позже",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(TextGenerationStates.editing)
async def editing_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием изменений.",
        reply_markup=back_to_menu_keyboard(),
    )
