from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.bot_decorators import check_user_limit, track_user_operation
from src.bot.keyboards import (
    back_to_menu_keyboard,
    text_generation_results_keyboard,
    struct_form_start_keyboard,
    struct_form_goal_keyboard,
    struct_form_platform_keyboard,
    struct_form_audience_keyboard,
    struct_form_style_keyboard,
    struct_form_length_keyboard,
    struct_form_skip_keyboard,
    overlay_mode_keyboard,
    overlay_position_keyboard,
    overlay_background_keyboard,
    overlay_font_keyboard,
    image_attachment_type_keyboard,
    image_attachment_position_keyboard,
)
from src.bot.states import TextGenerationStructStates
from src.services.text_overlay import TextOverlayConfig
from src.services.ai_manager import ai_manager
from src.bot.handlers.utils.image_overlay import build_image_with_overlay
from src.bot.handlers.utils.text_formatter import markdown_to_html
from src.services.service_decorators import TextLengthLimitError

router = Router()


def _extract_image_file_id(message: types.Message) -> str | None:
    if message.photo:
        return message.photo[-1].file_id

    if message.document:
        mime_type = message.document.mime_type or ""
        if mime_type.startswith("image/"):
            return message.document.file_id

    return None


def _struct_get_font_options(limit: int = 3) -> list[str]:
    service = ai_manager.image_generator.text_overlay
    if not service:
        return ["random"]

    fonts = [font for font in service.list_fonts() if font and font != "default"]
    if not fonts:
        fonts = []

    fonts = fonts[:limit]
    if "random" not in fonts:
        fonts.append("random")
    return fonts


def _struct_build_overlay_config(
    position: str | None, background: str | None
) -> TextOverlayConfig | None:
    if not position and (not background or background == "auto"):
        return None

    config = TextOverlayConfig()

    if position and position != "auto":
        config.position = position

    if background:
        if background == "dark":
            config.background_color = (0, 0, 0, 210)
            config.text_color = (255, 255, 255, 255)
        elif background == "light":
            config.background_color = (255, 255, 255, 235)
            config.text_color = (20, 20, 20, 255)
        elif background == "transparent":
            config.background_color = (0, 0, 0, 0)
            config.text_color = (255, 255, 255, 255)

    return config


async def _start_struct_post_generation(
    callback_or_message, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    user_id = callback_or_message.from_user.id
    await state.set_state(TextGenerationStructStates.waiting_results)
    return await generate_struct_post_with_image(
        callback_or_message, state, data, user_id, session
    )


async def _generate_struct_image(post_text: str, data: dict) -> bytes:
    overlay_mode = data.get("overlay_mode", "none")
    overlay_text = data.get("overlay_text")
    overlay_font = data.get("overlay_font")
    overlay_position = data.get("overlay_position")
    overlay_background = data.get("overlay_background")
    overlay_config = _struct_build_overlay_config(overlay_position, overlay_background)

    return await ai_manager.generate_image_from_post(
        post_text=post_text,
        include_info_block=(overlay_mode == "auto"),
        prepared_info_text=overlay_text if overlay_mode == "custom" else None,
        overlay_font=overlay_font,
        overlay_config=overlay_config,
    )


@router.callback_query(F.data == "text_gen:struct")
@check_user_limit()
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
        "Вы можете написать текст или <b>отправить голосовое сообщение</b>.",
        reply_markup=back_to_menu_keyboard(),
    )


# Вопрос 1: О каком событии пост?
@router.message(TextGenerationStructStates.question_1_event, F.text)
async def question_1_text_handler(message: types.Message, state: FSMContext):
    event_text = message.text.strip()

    if not event_text:
        return await message.answer(
            "Пожалуйста, отправьте текст или <b>голосовое сообщение</b>.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(event=event_text)
    await state.set_state(TextGenerationStructStates.question_2_description)

    return await message.answer(
        "📋 <b>Вопрос 2/10</b>\n\n"
        "Опишите событие подробнее или <b>отправьте голосовое сообщение</b>.\n\n"
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
        "Пожалуйста, отправьте текстовое сообщение или <b>голосовое сообщение</b> с описанием.",
        reply_markup=back_to_menu_keyboard(),
    )


# Вопрос 2: Описание события подробнее
@router.message(TextGenerationStructStates.question_2_description, F.text)
async def question_2_text_handler(message: types.Message, state: FSMContext):
    description_text = message.text.strip()

    if not description_text:
        return await message.answer(
            "Пожалуйста, отправьте текст или <b>голосовое сообщение</b>.",
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
        "Пожалуйста, отправьте текстовое сообщение или <b>голосовое сообщение</b> с описанием.",
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
    callback_or_message,
    state: FSMContext,
    data: dict,
    user_id: int,
    session: AsyncSession,
):
    is_callback = isinstance(callback_or_message, types.CallbackQuery)

    if is_callback:
        loading_msg = await callback_or_message.message.answer("⏳ Создаю пост...")
    else:
        loading_msg = await callback_or_message.answer("⏳ Создаю пост...")

    try:
        post = await ai_manager.generate_structured_form_post(
            user_id=user_id,
            session=session,
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

        image_bytes = await _generate_struct_image(post, data)

        await loading_msg.delete()
        await state.update_data(
            post=post,
            overlay_mode=data.get("overlay_mode", "none"),
            overlay_text=data.get("overlay_text")
            if data.get("overlay_mode") == "custom"
            else None,
            overlay_position=data.get("overlay_position"),
            overlay_background=data.get("overlay_background"),
            overlay_font=data.get("overlay_font"),
        )

        if is_callback:
            await callback_or_message.message.answer("✨ <b>Готово! Ваш пост:</b>")

            image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
            photo_message = await callback_or_message.message.answer_photo(
                photo=image_file, caption=markdown_to_html(post)
            )
            image_file_id = (
                photo_message.photo[-1].file_id if photo_message.photo else None
            )
            await state.update_data(image_file_id=image_file_id, has_image=True)

            await track_user_operation(user_id)

            return await callback_or_message.message.answer(
                "Выберите действие", reply_markup=text_generation_results_keyboard()
            )
        else:
            await callback_or_message.answer("✨ <b>Готово! Ваш пост:</b>")

            image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
            photo_message = await callback_or_message.answer_photo(
                photo=image_file, caption=markdown_to_html(post)
            )
            image_file_id = (
                photo_message.photo[-1].file_id if photo_message.photo else None
            )
            await state.update_data(image_file_id=image_file_id, has_image=True)

            await track_user_operation(user_id)

            return await callback_or_message.answer(
                "Выберите действие", reply_markup=text_generation_results_keyboard()
            )

    except TextLengthLimitError:
        await loading_msg.delete()
        error_msg = (
            "❌ Не удалось получить текст подходящей длины (до 1024 символов).\n"
            "Попробуйте заново."
        )
        if is_callback:
            return await callback_or_message.message.answer(
                error_msg,
                reply_markup=back_to_menu_keyboard(),
            )
        return await callback_or_message.answer(
            error_msg,
            reply_markup=back_to_menu_keyboard(),
        )

    except Exception:
        await loading_msg.delete()

        if is_callback:
            return await callback_or_message.message.answer(
                "❌ Произошла ошибка. Попробуйте ещё раз позже",
                reply_markup=back_to_menu_keyboard(),
            )
        else:
            return await callback_or_message.answer(
                "❌ Произошла ошибка. Попробуйте ещё раз позже",
                reply_markup=back_to_menu_keyboard(),
            )


# Вопрос 10: Дополнительная информация
@router.callback_query(
    F.data == "struct_skip:skip", TextGenerationStructStates.question_10_additional
)
async def question_10_skip_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(additional_info=None)
    await state.set_state(TextGenerationStructStates.image_overlay_mode)
    await callback.answer()

    return await callback.message.edit_text(
        "🖼 <b>Нужно ли добавить текст на картинку для поста?</b>",
        reply_markup=overlay_mode_keyboard(include_auto=True),
    )


@router.message(TextGenerationStructStates.question_10_additional, F.text)
async def question_10_additional_handler(message: types.Message, state: FSMContext):
    additional_text = message.text.strip()

    if not additional_text:
        return await message.answer(
            "Пожалуйста, укажите дополнительную информацию или нажмите 'Пропустить'.",
            reply_markup=struct_form_skip_keyboard(),
        )

    await state.update_data(additional_info=additional_text)
    await state.set_state(TextGenerationStructStates.image_overlay_mode)

    return await message.answer(
        "🖼 <b>Нужно ли добавить текст на картинку для поста?</b>",
        reply_markup=overlay_mode_keyboard(include_auto=True),
    )


@router.message(TextGenerationStructStates.question_10_additional)
async def question_10_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с дополнительной информацией или нажмите 'Пропустить'.",
        reply_markup=struct_form_skip_keyboard(),
    )


# Настройка изображения для структурированного поста
@router.callback_query(
    TextGenerationStructStates.image_overlay_mode, F.data.startswith("overlay_mode:")
)
async def struct_overlay_mode_handler(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    mode = callback.data.split(":")[1]
    await callback.answer()

    if mode == "none":
        await state.update_data(
            overlay_mode="none",
            overlay_text=None,
            overlay_position=None,
            overlay_background=None,
            overlay_font=None,
        )
        return await _start_struct_post_generation(callback, state, session)

    if mode == "custom":
        await state.update_data(overlay_mode="custom")
        await state.set_state(TextGenerationStructStates.image_overlay_text)
        return await callback.message.edit_text(
            "✍️ <b>Введите фразу для картинки</b>\n\n"
            "Например: «Регистрация открыта», «15 декабря 18:00», «Энергия добра».\n"
            "Фраза должна быть короткой и информативной.",
            reply_markup=back_to_menu_keyboard(),
        )

    # Автоматический текст
    await state.update_data(overlay_mode="auto", overlay_text=None)
    await state.set_state(TextGenerationStructStates.image_overlay_position)

    return await callback.message.edit_text(
        "📍 <b>Где разместить текст на изображении?</b>",
        reply_markup=overlay_position_keyboard(),
    )


@router.message(TextGenerationStructStates.image_overlay_text, F.text)
async def struct_overlay_text_handler(message: types.Message, state: FSMContext):
    text_value = message.text.strip()

    if not text_value:
        return await message.answer(
            "Пожалуйста, отправьте текст для подписи.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(overlay_text=text_value)
    await state.set_state(TextGenerationStructStates.image_overlay_position)

    return await message.answer(
        "📍 <b>Где разместить текст на изображении?</b>",
        reply_markup=overlay_position_keyboard(),
    )


@router.message(TextGenerationStructStates.image_overlay_text)
async def struct_overlay_text_invalid(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте текстовую подпись.", reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(
    TextGenerationStructStates.image_overlay_position,
    F.data.startswith("overlay_position:"),
)
async def struct_overlay_position_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    position = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(overlay_position=None if position == "auto" else position)
    await state.set_state(TextGenerationStructStates.image_overlay_background)

    return await callback.message.edit_text(
        "🎨 <b>Выберите фон для текста</b>", reply_markup=overlay_background_keyboard()
    )


@router.callback_query(
    TextGenerationStructStates.image_overlay_background,
    F.data.startswith("overlay_bg:"),
)
async def struct_overlay_background_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    background = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(
        overlay_background=None if background == "auto" else background
    )
    await state.set_state(TextGenerationStructStates.image_overlay_font)

    font_options = _struct_get_font_options()

    return await callback.message.edit_text(
        "🔠 <b>Выберите стиль шрифта</b>",
        reply_markup=overlay_font_keyboard(font_options),
    )


@router.callback_query(
    TextGenerationStructStates.image_overlay_font, F.data.startswith("overlay_font:")
)
async def struct_overlay_font_handler(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    font_value = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(overlay_font=None if font_value == "random" else font_value)
    return await _start_struct_post_generation(callback, state, session)


# Обработка результатов


@router.callback_query(
    F.data == "text_result:change_image", TextGenerationStructStates.waiting_results
)
@check_user_limit()
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
        image_bytes = await _generate_struct_image(post, data)

        await loading_msg.delete()

        # Отправляем новое изображение
        image_file = BufferedInputFile(image_bytes, filename="post_image.jpg")
        photo_message = await callback.message.answer_photo(
            photo=image_file, caption=markdown_to_html(post)
        )
        image_file_id = photo_message.photo[-1].file_id if photo_message.photo else None
        await state.update_data(image_file_id=image_file_id, has_image=True)

        await track_user_operation(callback.from_user.id)

        return await callback.message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except Exception:
        await loading_msg.delete()
        await callback.message.answer(
            "❌ Ошибка при создании изображения. Попробуйте ещё раз позже",
            reply_markup=text_generation_results_keyboard(),
        )


@router.callback_query(
    F.data == "text_result:add_overlay", TextGenerationStructStates.waiting_results
)
async def struct_add_overlay_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    image_file_id = data.get("image_file_id")

    if not image_file_id:
        await callback.answer("Сначала сгенерируйте изображение", show_alert=True)
        return

    await state.set_state(TextGenerationStructStates.adding_overlay)
    await state.update_data(
        pending_overlay_file_id=None,
        pending_overlay_type=None,
    )

    await callback.answer()
    return await callback.message.answer(
        "📎 Пришлите логотип или фотографию, которую нужно добавить на картинку.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationStructStates.adding_overlay, F.photo | F.document)
async def struct_overlay_file_handler(message: types.Message, state: FSMContext):
    file_id = _extract_image_file_id(message)

    if not file_id:
        return await message.answer(
            "Пожалуйста, отправьте изображение (фото или файл).",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(pending_overlay_file_id=file_id)
    await state.set_state(TextGenerationStructStates.adding_overlay_type)
    return await message.answer(
        "Выберите, как использовать изображение:",
        reply_markup=image_attachment_type_keyboard(),
    )


@router.message(TextGenerationStructStates.adding_overlay)
async def struct_overlay_file_invalid(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте изображение (фото или файл).",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(
    TextGenerationStructStates.adding_overlay_type,
    F.data.startswith("image_asset:type:"),
)
async def struct_overlay_type_handler(callback: types.CallbackQuery, state: FSMContext):
    _, _, value = callback.data.split(":")

    if value == "cancel":
        await state.set_state(TextGenerationStructStates.waiting_results)
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await callback.answer("Добавление отменено")
        return await callback.message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    if value not in {"logo", "photo"}:
        await callback.answer("Используйте кнопки ниже", show_alert=True)
        return

    await state.update_data(pending_overlay_type=value)
    await state.set_state(TextGenerationStructStates.adding_overlay_position)
    await callback.answer()
    return await callback.message.answer(
        "📍 Где разместить изображение?",
        reply_markup=image_attachment_position_keyboard(),
    )


@router.message(TextGenerationStructStates.adding_overlay_type)
async def struct_overlay_type_invalid(message: types.Message):
    return await message.answer(
        "Пожалуйста, выберите вариант с помощью кнопок.",
        reply_markup=image_attachment_type_keyboard(),
    )


@router.callback_query(
    TextGenerationStructStates.adding_overlay_position,
    F.data.startswith("image_asset:pos:"),
)
async def struct_overlay_image_position_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    _, _, value = callback.data.split(":")

    if value == "cancel":
        await state.set_state(TextGenerationStructStates.waiting_results)
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
        await state.set_state(TextGenerationStructStates.waiting_results)
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await callback.answer("Изображение не найдено", show_alert=True)
        return await callback.message.answer(
            "❌ Не удалось подготовить изображение. Попробуйте ещё раз.",
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
                merged_bytes, filename="struct_post_image_with_overlay.png"
            ),
            caption=markdown_to_html(post_text),
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
        await state.set_state(TextGenerationStructStates.waiting_results)

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
        await state.set_state(TextGenerationStructStates.waiting_results)

        return await callback.message.answer(
            "❌ Не удалось добавить изображение. Попробуйте другой файл.",
            reply_markup=text_generation_results_keyboard(),
        )


@router.message(TextGenerationStructStates.adding_overlay_position)
async def struct_overlay_position_invalid(message: types.Message):
    return await message.answer(
        "Пожалуйста, выберите позицию с помощью кнопок.",
        reply_markup=image_attachment_position_keyboard(),
    )


@router.callback_query(
    F.data == "text_result:edit", TextGenerationStructStates.waiting_results
)
@check_user_limit()
async def text_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStructStates.editing)
    await callback.answer()
    return await callback.message.answer(
        "✏️ <b>Редактирование поста</b>\n\n"
        "Что нужно изменить в посте? Опишите ваши пожелания.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationStructStates.editing, F.text)
async def editing_handler(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    edit_request = message.text.strip()

    if not edit_request:
        return await message.answer(
            "Пожалуйста, опишите, что нужно изменить.",
            reply_markup=back_to_menu_keyboard(),
        )

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
        # Обновляем пост
        updated_post = await ai_manager.generate_free_text_post(
            user_id=user_id,
            session=session,
            user_idea=f"Исходный пост:\n{original_post}\n\nИзменения: {edit_request}",
            style="разговорный",
        )

        await loading_msg.edit_text("✨ Сохраняю изменения...")
        await loading_msg.delete()
        await state.update_data(post=updated_post)
        await state.set_state(TextGenerationStructStates.waiting_results)

        await message.answer("✨ <b>Пост обновлён:</b>")
        await message.answer(markdown_to_html(updated_post))

        if image_file_id:
            photo_message = await message.answer_photo(
                photo=image_file_id, caption=markdown_to_html(updated_post)
            )
            new_image_file_id = (
                photo_message.photo[-1].file_id
                if photo_message.photo
                else image_file_id
            )
            await state.update_data(image_file_id=new_image_file_id, has_image=True)

        await track_user_operation(user_id)

        return await message.answer(
            "Выберите действие", reply_markup=text_generation_results_keyboard()
        )

    except TextLengthLimitError:
        await loading_msg.delete()
        return await message.answer(
            "❌ Не удалось получить текст подходящей длины (до 1024 символов).\n"
            "Попробуйте уточнить пожелания.",
            reply_markup=back_to_menu_keyboard(),
        )

    except Exception:
        await loading_msg.delete()
        return await message.answer(
            "❌ Произошла ошибка. Попробуйте позже",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(TextGenerationStructStates.editing)
async def editing_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием изменений.",
        reply_markup=back_to_menu_keyboard(),
    )
