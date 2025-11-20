from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

from src.bot.keyboards import (
    back_to_menu_keyboard,
    text_generation_results_keyboard,
    main_menu_keyboard,
    struct_form_start_keyboard,
    struct_form_goal_keyboard,
    struct_form_platform_keyboard,
    struct_form_audience_keyboard,
    struct_form_style_keyboard,
    struct_form_length_keyboard,
    struct_form_skip_keyboard,
)
from src.bot.states import TextGenerationStructStates, MainMenuStates
from src.services.ai_manager import AIManager

router = Router()
ai_manager = AIManager()


@router.callback_query(F.data == "text_gen:struct")
async def struct_form_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStructStates.method_selection)
    await callback.answer()
    return await callback.message.edit_text(
        "📋 <b>Структурированная форма</b>\n\n"
        "Мы зададим вам 10 вопросов, чтобы создать идеальный пост для вашего события.\n\n"
        "Это займёт всего несколько минут!",
        reply_markup=struct_form_start_keyboard(),
    )


@router.callback_query(F.data == "struct_form:start")
async def struct_form_start_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStructStates.question_1_event)
    await callback.answer()
    return await callback.message.edit_text(
        "📋 <b>Вопрос 1/10</b>\n\n"
        "О каком событии пост?\n\n"
        "Например: IT-хакатон 'Энергия добра'.\n\n"
        "Вы можете написать текст или отправить голосовое сообщение.",
        reply_markup=back_to_menu_keyboard(),
    )


# Вопрос 1: О каком событии пост?
@router.message(TextGenerationStructStates.question_1_event, F.text)
async def question_1_text_handler(message: types.Message, state: FSMContext):
    event_text = message.text.strip()

    if not event_text:
        return await message.answer(
            "Пожалуйста, отправьте текст или голосовое сообщение.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(event=event_text)
    await state.set_state(TextGenerationStructStates.question_2_description)

    return await message.answer(
        "📋 <b>Вопрос 2/10</b>\n\n"
        "Опишите событие подробнее или отправьте голосовое сообщение.\n\n"
        "Расскажите о формате, участниках, дате и времени, ключевых деталях и результатах.\n\n"
        "<i>Например: событие проходило с 14 по 16 ноября в онлайн формате, участвовали более 300 человек, "
        "было 3 кейса: телеграм-бот для создания ИИ контента, онлайн-навигатор по социальным проектам, "
        "информационный портал с интерактивной картой.</i>",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationStructStates.question_1_event, F.voice)
async def question_1_voice_handler(message: types.Message, state: FSMContext):
    if not message.voice:
        return await message.answer(
            "Пожалуйста, отправьте голосовое сообщение.",
            reply_markup=back_to_menu_keyboard(),
        )

    transcribe_msg = await message.answer("⏳ Распознаю речь...")

    try:
        file = await message.bot.get_file(message.voice.file_id)
        audio_file = await message.bot.download_file(file.file_path)
        audio_data = audio_file.read()

        event_text = await ai_manager.transcribe_voice(
            audio_data=audio_data, audio_format="opus"
        )

        await transcribe_msg.delete()

        if not event_text or not event_text.strip():
            return await message.answer(
                "Не удалось распознать речь. Попробуйте отправить голосовое сообщение ещё раз.",
                reply_markup=back_to_menu_keyboard(),
            )

        await message.answer(f"Вы сказали: {event_text}")

        await state.update_data(event=event_text.strip())
        await state.set_state(TextGenerationStructStates.question_2_description)

        return await message.answer(
            "📋 <b>Вопрос 2/10</b>\n\n"
            "Опишите событие подробнее.\n\n"
            "Что произойдёт? Кто участвует? Какие детали важны?",
            reply_markup=back_to_menu_keyboard(),
        )

    except Exception as e:
        await transcribe_msg.delete()
        return await message.answer(
            f"❌ Ошибка при распознавании речи: {str(e)}",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(TextGenerationStructStates.question_1_event)
async def question_1_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение или голосовое сообщение с описанием.",
        reply_markup=back_to_menu_keyboard(),
    )


# Вопрос 2: Описание события подробнее
@router.message(TextGenerationStructStates.question_2_description, F.text)
async def question_2_text_handler(message: types.Message, state: FSMContext):
    description_text = message.text.strip()

    if not description_text:
        return await message.answer(
            "Пожалуйста, отправьте текст или голосовое сообщение.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(description=description_text)
    await state.set_state(TextGenerationStructStates.question_3_goal)

    return await message.answer(
        "📋 <b>Вопрос 3/10</b>\n\nКакова главная цель поста?",
        reply_markup=struct_form_goal_keyboard(),
    )


@router.message(TextGenerationStructStates.question_2_description, F.voice)
async def question_2_voice_handler(message: types.Message, state: FSMContext):
    if not message.voice:
        return await message.answer(
            "Пожалуйста, отправьте голосовое сообщение.",
            reply_markup=back_to_menu_keyboard(),
        )

    transcribe_msg = await message.answer("⏳ Распознаю речь...")

    try:
        file = await message.bot.get_file(message.voice.file_id)
        audio_file = await message.bot.download_file(file.file_path)
        audio_data = audio_file.read()

        description_text = await ai_manager.transcribe_voice(
            audio_data=audio_data, audio_format="opus"
        )

        await transcribe_msg.delete()

        if not description_text or not description_text.strip():
            return await message.answer(
                "Не удалось распознать речь. Попробуйте отправить голосовое сообщение ещё раз.",
                reply_markup=back_to_menu_keyboard(),
            )

        await message.answer(f"Вы сказали: {description_text}")

        await state.update_data(description=description_text.strip())
        await state.set_state(TextGenerationStructStates.question_3_goal)

        return await message.answer(
            "📋 <b>Вопрос 3/10</b>\n\nКакова главная цель поста?",
            reply_markup=struct_form_goal_keyboard(),
        )

    except Exception as e:
        await transcribe_msg.delete()
        return await message.answer(
            f"❌ Ошибка при распознавании речи: {str(e)}",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(TextGenerationStructStates.question_2_description)
async def question_2_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение или голосовое сообщение с описанием.",
        reply_markup=back_to_menu_keyboard(),
    )


# Вопрос 3: Главная цель поста
@router.callback_query(
    F.data.startswith("struct_goal:"), TextGenerationStructStates.question_3_goal
)
async def question_3_goal_handler(callback: types.CallbackQuery, state: FSMContext):
    goal_data = callback.data.split(":")[1]

    if goal_data == "other":
        await state.set_state(TextGenerationStructStates.question_3_goal_other)
        await callback.answer()
        return await callback.message.edit_text(
            "📋 <b>Вопрос 3/10</b>\n\nОпишите главную цель поста своими словами:",
            reply_markup=back_to_menu_keyboard(),
        )

    goal_map = {
        "result": "struct_goal:result",
        "volunteers": "struct_goal:volunteers",
        "donations": "struct_goal:donations",
        "work": "struct_goal:work",
        "thanks": "struct_goal:thanks",
        "announcement": "struct_goal:announcement",
    }

    goal_value = goal_map.get(goal_data, f"struct_goal:{goal_data}")
    await state.update_data(goal=goal_value)
    await state.set_state(TextGenerationStructStates.question_4_date)
    await callback.answer()

    return await callback.message.edit_text(
        "📋 <b>Вопрос 4/10</b>\n\n"
        "Дата и время события??\n\n"
        "<i>Например: 15 декабря в 18:00 или с 14 по 16 ноября</i>",
        reply_markup=struct_form_skip_keyboard(),
    )


@router.message(TextGenerationStructStates.question_3_goal_other, F.text)
async def question_3_goal_other_handler(message: types.Message, state: FSMContext):
    goal_text = message.text.strip()

    if not goal_text:
        return await message.answer(
            "Пожалуйста, опишите главную цель поста.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(goal=f"other:{goal_text}")
    await state.set_state(TextGenerationStructStates.question_4_date)

    return await message.answer(
        "📋 <b>Вопрос 4/10</b>\n\n"
        "Дата и время события??\n\n"
        "<i>Например: 15 декабря в 18:00 или с 14 по 16 ноября</i>",
        reply_markup=struct_form_skip_keyboard(),
    )


@router.message(TextGenerationStructStates.question_3_goal_other)
async def question_3_goal_other_invalid_handler(
    message: types.Message, state: FSMContext
):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием цели.",
        reply_markup=back_to_menu_keyboard(),
    )


# Вопрос 4: Дата и время
@router.callback_query(
    F.data == "struct_skip:skip", TextGenerationStructStates.question_4_date
)
async def question_4_skip_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(date=None)
    await state.set_state(TextGenerationStructStates.question_5_location)
    await callback.answer()

    return await callback.message.edit_text(
        "📋 <b>Вопрос 5/10</b>\n\n"
        "Где состоится событие? (Место проведения)\n\n"
        "<i>Например: Парк Горького или онлайн</i>",
        reply_markup=struct_form_skip_keyboard(),
    )


@router.message(TextGenerationStructStates.question_4_date, F.text)
async def question_4_date_handler(message: types.Message, state: FSMContext):
    date_text = message.text.strip()

    if not date_text:
        return await message.answer(
            "Пожалуйста, укажите дату и время или нажмите 'Пропустить'.",
            reply_markup=struct_form_skip_keyboard(),
        )

    await state.update_data(date=date_text)
    await state.set_state(TextGenerationStructStates.question_5_location)

    return await message.answer(
        "📋 <b>Вопрос 5/10</b>\n\n"
        "Где состоится событие? (Место проведения)\n\n"
        "<i>Например: Парк Горького, главная сцена</i>",
        reply_markup=struct_form_skip_keyboard(),
    )


@router.message(TextGenerationStructStates.question_4_date)
async def question_4_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с датой и временем или нажмите 'Пропустить'.",
        reply_markup=struct_form_skip_keyboard(),
    )


# Вопрос 5: Место проведения
@router.callback_query(
    F.data == "struct_skip:skip", TextGenerationStructStates.question_5_location
)
async def question_5_skip_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(location=None)
    await state.set_state(TextGenerationStructStates.question_6_platform)
    await callback.answer()

    return await callback.message.edit_text(
        "📋 <b>Вопрос 6/10</b>\n\nНа какой площадке будет опубликован пост?",
        reply_markup=struct_form_platform_keyboard(),
    )


@router.message(TextGenerationStructStates.question_5_location, F.text)
async def question_5_location_handler(message: types.Message, state: FSMContext):
    location_text = message.text.strip()

    if not location_text:
        return await message.answer(
            "Пожалуйста, укажите место проведения или нажмите 'Пропустить'.",
            reply_markup=struct_form_skip_keyboard(),
        )

    await state.update_data(location=location_text)
    await state.set_state(TextGenerationStructStates.question_6_platform)

    return await message.answer(
        "📋 <b>Вопрос 6/10</b>\n\nНа какой площадке будет опубликован пост?",
        reply_markup=struct_form_platform_keyboard(),
    )


@router.message(TextGenerationStructStates.question_5_location)
async def question_5_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с местом проведения или нажмите 'Пропустить'.",
        reply_markup=struct_form_skip_keyboard(),
    )


# Вопрос 6: Площадка публикации
@router.callback_query(
    F.data.startswith("struct_platform:"),
    TextGenerationStructStates.question_6_platform,
)
async def question_6_platform_handler(callback: types.CallbackQuery, state: FSMContext):
    platform_data = callback.data.split(":")[1]
    await state.update_data(platform=platform_data)
    await state.set_state(TextGenerationStructStates.question_7_audience)
    await callback.answer()

    return await callback.message.edit_text(
        "📋 <b>Вопрос 7/10</b>\n\nКто ваша целевая аудитория?",
        reply_markup=struct_form_audience_keyboard(),
    )


# Вопрос 7: Целевая аудитория
@router.callback_query(
    F.data.startswith("struct_audience:"),
    TextGenerationStructStates.question_7_audience,
)
async def question_7_audience_handler(callback: types.CallbackQuery, state: FSMContext):
    audience_data = callback.data.split(":")[1]
    await state.update_data(audience=audience_data)
    await state.set_state(TextGenerationStructStates.question_8_style)
    await callback.answer()

    return await callback.message.edit_text(
        "📋 <b>Вопрос 8/10</b>\n\nКакой стиль текста вам нужен?",
        reply_markup=struct_form_style_keyboard(),
    )


# Вопрос 8: Стиль текста
@router.callback_query(
    F.data.startswith("struct_style:"), TextGenerationStructStates.question_8_style
)
async def question_8_style_handler(callback: types.CallbackQuery, state: FSMContext):
    style_data = callback.data.split(":")[1]
    await state.update_data(style=style_data)
    await state.set_state(TextGenerationStructStates.question_9_length)
    await callback.answer()

    return await callback.message.edit_text(
        "📋 <b>Вопрос 9/10</b>\n\nКакой объём текста вам нужен?",
        reply_markup=struct_form_length_keyboard(),
    )


# Вопрос 9: Объём текста
@router.callback_query(
    F.data.startswith("struct_length:"), TextGenerationStructStates.question_9_length
)
async def question_9_length_handler(callback: types.CallbackQuery, state: FSMContext):
    length_data = callback.data.split(":")[1]
    await state.update_data(length=length_data)
    await state.set_state(TextGenerationStructStates.question_10_additional)
    await callback.answer()

    return await callback.message.edit_text(
        "📋 <b>Вопрос 10/10</b>\n\n"
        "Есть ли дополнительная информация, которую нужно учесть?\n\n"
        "<i>Например: особые требования, важные детали, контакты и т.д.</i>",
        reply_markup=struct_form_skip_keyboard(),
    )


async def generate_struct_post_with_image(
    callback_or_message, state: FSMContext, data: dict, user_id: int
):
    is_callback = isinstance(callback_or_message, types.CallbackQuery)

    if is_callback:
        loading_msg = await callback_or_message.message.answer("⏳ Создаю пост...")
    else:
        loading_msg = await callback_or_message.answer("⏳ Создаю пост...")

    try:
        post = await ai_manager.generate_structured_form_post(
            user_id=user_id,
            event=data.get("event", ""),
            description=data.get("description", ""),
            goal=data.get("goal", "struct_goal:work"),
            date=data.get("date"),
            location=data.get("location"),
            platform=data.get("platform", "universal"),
            audience=data.get("audience", "broad"),
            style=data.get("style", "warm"),
            length=data.get("length", "medium"),
            additional_info=data.get("additional_info"),
        )

        await loading_msg.edit_text("⏳ Создаю изображение для поста...")

        image_bytes = await ai_manager.generate_image_from_post(post_text=post)

        await loading_msg.delete()
        await state.update_data(post=post)

        if is_callback:
            await callback_or_message.message.answer("✨ <b>Готово! Ваш пост:</b>")
            await callback_or_message.message.answer(f"{post}")

            image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
            await callback_or_message.message.answer_photo(
                photo=image_file, caption="🖼 Изображение для вашего поста"
            )

            return await callback_or_message.message.answer(
                "Выберите действие", reply_markup=text_generation_results_keyboard()
            )
        else:
            await callback_or_message.answer("✨ <b>Готово! Ваш пост:</b>")
            await callback_or_message.answer(f"{post}")

            image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
            await callback_or_message.answer_photo(
                photo=image_file, caption="🖼 Изображение для вашего поста"
            )

            return await callback_or_message.answer(
                "Выберите действие", reply_markup=text_generation_results_keyboard()
            )

    except Exception as e:
        await loading_msg.delete()

        if is_callback:
            return await callback_or_message.message.answer(
                f"❌ Произошла ошибка: {str(e)}", reply_markup=back_to_menu_keyboard()
            )
        else:
            return await callback_or_message.answer(
                f"❌ Произошла ошибка: {str(e)}", reply_markup=back_to_menu_keyboard()
            )


# Вопрос 10: Дополнительная информация
@router.callback_query(
    F.data == "struct_skip:skip", TextGenerationStructStates.question_10_additional
)
async def question_10_skip_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(additional_info=None)
    await state.set_state(TextGenerationStructStates.waiting_results)
    await callback.answer()

    data = await state.get_data()
    user_id = callback.from_user.id

    return await generate_struct_post_with_image(callback, state, data, user_id)


@router.message(TextGenerationStructStates.question_10_additional, F.text)
async def question_10_additional_handler(message: types.Message, state: FSMContext):
    additional_text = message.text.strip()

    if not additional_text:
        return await message.answer(
            "Пожалуйста, укажите дополнительную информацию или нажмите 'Пропустить'.",
            reply_markup=struct_form_skip_keyboard(),
        )

    await state.update_data(additional_info=additional_text)
    await state.set_state(TextGenerationStructStates.waiting_results)

    data = await state.get_data()
    user_id = message.from_user.id

    return await generate_struct_post_with_image(message, state, data, user_id)


@router.message(TextGenerationStructStates.question_10_additional)
async def question_10_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с дополнительной информацией или нажмите 'Пропустить'.",
        reply_markup=struct_form_skip_keyboard(),
    )


# Обработка результатов
@router.callback_query(
    F.data == "text_result:ok", TextGenerationStructStates.waiting_results
)
async def text_result_ok_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Рад был помочь! 🎉")
    return await callback.message.answer(
        "👋 Главное меню", reply_markup=main_menu_keyboard()
    )


@router.callback_query(
    F.data == "text_result:change_image", TextGenerationStructStates.waiting_results
)
async def text_result_change_image_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    """Обработка кнопки 'Поменять картинку'"""
    data = await state.get_data()
    post = data.get("post", "")

    if not post:
        await callback.answer("❌ Пост не найден", show_alert=True)
        return

    await callback.answer()
    loading_msg = await callback.message.answer("⏳ Создаю новое изображение...")

    try:
        # Создаём новое изображение
        image_bytes = await ai_manager.generate_image_from_post(post_text=post)

        await loading_msg.delete()

        # Отправляем новое изображение
        image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
        await callback.message.answer_photo(
            photo=image_file, caption="🖼 Новое изображение для вашего поста"
        )

        await callback.message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except Exception as e:
        await loading_msg.delete()
        await callback.message.answer(
            f"❌ Ошибка при создании изображения: {str(e)}",
            reply_markup=text_generation_results_keyboard(),
        )


@router.callback_query(
    F.data == "text_result:edit", TextGenerationStructStates.waiting_results
)
async def text_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStructStates.editing)
    await callback.answer()
    return await callback.message.answer(
        "✏️ <b>Редактирование поста</b>\n\n"
        "Что нужно изменить в посте? Опишите ваши пожелания.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationStructStates.editing, F.text)
async def editing_handler(message: types.Message, state: FSMContext):
    edit_request = message.text.strip()

    if not edit_request:
        return await message.answer(
            "Пожалуйста, опишите, что нужно изменить.",
            reply_markup=back_to_menu_keyboard(),
        )

    data = await state.get_data()
    original_post = data.get("post", "")

    if not original_post:
        return await message.answer(
            "❌ Не найден исходный пост для редактирования.",
            reply_markup=back_to_menu_keyboard(),
        )

    user_id = message.from_user.id
    loading_msg = await message.answer("⏳ Обновляю пост...")

    try:
        # Обновляем пост
        updated_post = await ai_manager.generate_free_text_post(
            user_id=user_id,
            user_idea=f"Исходный пост:\n{original_post}\n\nИзменения: {edit_request}",
            style="разговорный",
        )

        await loading_msg.edit_text("⏳ Создаю новое изображение...")

        # Создаём новое изображение
        image_bytes = await ai_manager.generate_image_from_post(post_text=updated_post)

        await loading_msg.delete()
        await state.update_data(post=updated_post)
        await state.set_state(TextGenerationStructStates.waiting_results)

        await message.answer("✨ <b>Пост обновлён:</b>")
        await message.answer(f"{updated_post}")

        image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
        await message.answer_photo(
            photo=image_file, caption="🖼 Обновлённое изображение для поста"
        )

        return await message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except Exception as e:
        await loading_msg.delete()
        return await message.answer(
            f"❌ Произошла ошибка: {str(e)}", reply_markup=back_to_menu_keyboard()
        )


@router.message(TextGenerationStructStates.editing)
async def editing_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием изменений.",
        reply_markup=back_to_menu_keyboard(),
    )
