import logging
from aiogram import types, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

from src.bot.bot_decorators import track_user_operation, check_user_limit
from src.bot.keyboards import (
    back_to_menu_keyboard,
    image_style_keyboard,
    image_colors_keyboard,
    image_generation_results_keyboard,
    main_menu_keyboard,
    image_mode_keyboard,
    overlay_mode_keyboard,
    overlay_position_keyboard,
    overlay_background_keyboard,
    overlay_font_keyboard,
    image_attachment_type_keyboard,
    image_attachment_position_keyboard,
)
from src.bot.states import ImageGenerationStates, MainMenuStates
from src.services.text_overlay import TextOverlayConfig
from src.services.ai_manager import ai_manager
from src.bot.handlers.utils.image_overlay import build_image_with_overlay

router = Router()
logger = logging.getLogger(__name__)


def _extract_image_file_id(message: types.Message) -> str | None:
    if message.photo:
        return message.photo[-1].file_id

    if message.document:
        mime_type = message.document.mime_type or ""
        if mime_type.startswith("image/"):
            return message.document.file_id

    return None


def _get_font_options(limit: int = 3) -> list[str]:
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


def _build_overlay_config(
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


async def _start_manual_image_generation(
    callback: types.CallbackQuery, state: FSMContext
):
    data = await state.get_data()
    description = data.get("description", "")
    style = data.get("style", "")
    colors = data.get("colors", "")
    style_name = data.get("style_name", "")
    colors_name = data.get("colors_name", "")

    if not description:
        await callback.answer()
        return await callback.message.edit_text(
            "❌ Ошибка: не указано описание изображения. Пожалуйста, начните заново.",
            reply_markup=back_to_menu_keyboard(),
        )

    loading_msg = await callback.message.edit_text(
        "⏳ Создаю изображение...\n\n"
        f"<b>Описание:</b> {description}\n"
        f"<b>Стиль:</b> {style_name or style}\n"
        f"<b>Цвета:</b> {colors_name or colors}"
    )

    await state.set_state(ImageGenerationStates.waiting_results)

    try:
        style_prompts = {
            "realistic": "реалистичная фотография, высокая детализация",
            "illustration": "художественная иллюстрация, рисунок",
            "minimalism": "минималистичный стиль, простота, чистые линии",
            "poster": "стиль постера или афиши, яркий, привлекающий внимание",
            "business": "деловой стиль, профессиональный вид",
        }

        color_prompts = {
            "warm": "тёплые цвета (красный, оранжевый, жёлтый)",
            "cold": "холодные цвета (синий, голубой, зелёный)",
            "bright": "яркие и контрастные цвета",
            "neutral": "нейтральные и пастельные тона",
            "auto": "",
        }

        style_desc = style_prompts.get(style, "")
        color_desc = color_prompts.get(colors, "")

        full_prompt = f"{description}. {style_desc}"
        if color_desc:
            full_prompt += f". {color_desc}"

        overlay_text = data.get("overlay_text")
        overlay_font = data.get("overlay_font")
        overlay_position = data.get("overlay_position")
        overlay_background = data.get("overlay_background")
        overlay_config = _build_overlay_config(overlay_position, overlay_background)

        image_bytes = await ai_manager.generate_image(
            prompt=full_prompt,
            width=1024,
            height=1024,
            overlay_text=overlay_text,
            overlay_font=overlay_font,
            overlay_config=overlay_config,
        )

        try:
            await loading_msg.delete()
        except Exception:
            pass

        await state.update_data(
            last_prompt=full_prompt,
            last_overlay_text=overlay_text,
            last_overlay_font=overlay_font,
            last_overlay_position=overlay_position,
            last_overlay_background=overlay_background,
        )

        caption = "✅ <b>Готово! Вот ваше изображение.</b>"
        photo_message = await callback.message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="generated_image.jpg"),
            caption=caption,
        )
        result_file_id = (
            photo_message.photo[-1].file_id if photo_message.photo else None
        )
        await state.update_data(
            last_result_file_id=result_file_id,
            last_result_caption=caption,
        )

        await track_user_operation(user_id=callback.from_user.id)

        return await callback.message.answer(
            "Выберите действие:", reply_markup=image_generation_results_keyboard()
        )

    except Exception:
        try:
            await loading_msg.delete()
        except Exception:
            pass
        return await callback.message.answer(
            "❌ Произошла ошибка при генерации изображения\n\n"
            "Попробуйте ещё раз или вернитесь в главное меню.",
            reply_markup=back_to_menu_keyboard(),
        )


@router.callback_query(F.data == "main_menu:image_generation")
async def image_generation_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.mode_selection)
    await callback.answer()
    return await callback.message.edit_text(
        "🎨 <b>Генерация картинки</b>\n\nВыберите режим работы:",
        reply_markup=image_mode_keyboard(),
    )


@router.callback_query(F.data == "image_mode:create")
@check_user_limit()
async def image_mode_create_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.description)
    await state.update_data(mode="create", uploaded_files=[])
    await callback.answer()
    return await callback.message.edit_text(
        "🎨 <b>Создание нового изображения</b>\n\n"
        "<b>Вопрос 1/3:</b> Опишите, какую картинку нужно создать.\n\n"
        "<i>💡 Чем подробнее описание, тем лучше результат!</i>\n\n"
        "<i>Примеры хороших описаний:</i>\n"
        '• "Волонтёры убирают мусор на берегу озера, собирают его в мешки. '
        'На заднем плане озеро и деревья, солнечная погода."\n'
        '• "Дети читают книги в библиотеке, уютная атмосфера, тёплый свет"\n'
        '• "Логотип благотворительного фонда с изображением дома и сердца"',
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "image_mode:edit")
@check_user_limit()
async def image_mode_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.upload_for_edit)
    await state.update_data(mode="edit", uploaded_files=[])
    await callback.answer()
    return await callback.message.edit_text(
        "✏️ <b>Редактирование изображения</b>\n\n"
        "Загрузите изображение, которое нужно отредактировать.\n\n"
        "<i>Вы сможете:</i>\n"
        "• Исправить детали\n"
        "• Изменить стиль\n"
        "• Добавить или убрать элементы\n"
        "• Улучшить качество",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "image_mode:example")
@check_user_limit()
async def image_mode_example_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.upload_example)
    await state.update_data(mode="example", uploaded_files=[])
    await callback.answer()
    return await callback.message.edit_text(
        "📋 <b>Создание по примеру</b>\n\n"
        "Загрузите изображение-пример.\n\n"
        "<i>Я создам новое изображение в похожем стиле, с похожей композицией или цветовой гаммой.</i>",
        reply_markup=back_to_menu_keyboard(),
    )


# ============================================================================
# РЕЖИМ: РЕДАКТИРОВАНИЕ ИЗОБРАЖЕНИЯ
# ============================================================================


@router.message(ImageGenerationStates.upload_for_edit, F.photo)
async def upload_for_edit_photo_handler(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id

    await state.update_data(source_file_id=file_id)
    await state.set_state(ImageGenerationStates.edit_prompt)

    return await message.answer(
        "✅ Изображение загружено!\n\n"
        "Теперь опишите, что нужно изменить.\n\n"
        "<i>Примеры:</i>\n"
        '• "Сделай фон более ярким"\n'
        '• "Убери человека слева"\n'
        "• \"Добавь текст 'Спасибо волонтёрам'\"\n"
        '• "Измени стиль на акварельный"\n'
        '• "Улучши качество и детализацию"',
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ImageGenerationStates.upload_for_edit, F.document)
async def upload_for_edit_document_handler(message: types.Message, state: FSMContext):
    document = message.document

    if not document.mime_type or not document.mime_type.startswith("image/"):
        return await message.answer(
            "Пожалуйста, загрузите изображение (фото или файл с изображением).",
            reply_markup=back_to_menu_keyboard(),
        )

    file_id = document.file_id

    await state.update_data(source_file_id=file_id)
    await state.set_state(ImageGenerationStates.edit_prompt)

    return await message.answer(
        "✅ Изображение загружено!\n\nТеперь опишите, что нужно изменить.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ImageGenerationStates.upload_for_edit)
async def upload_for_edit_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте изображение (фото или файл).",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ImageGenerationStates.edit_prompt, F.text)
async def edit_prompt_handler(message: types.Message, state: FSMContext):
    edit_prompt = message.text.strip()

    if not edit_prompt:
        return await message.answer(
            "Пожалуйста, опишите, что нужно изменить.",
            reply_markup=back_to_menu_keyboard(),
        )

    data = await state.get_data()
    source_file_id = data.get("source_file_id")

    if not source_file_id:
        return await message.answer(
            "❌ Ошибка: изображение не найдено. Начните заново.",
            reply_markup=back_to_menu_keyboard(),
        )

    loading_msg = await message.answer(
        "⏳ Редактирую изображение...\n\n"
        "<i>Этап 1/2: Анализирую исходное изображение...</i>"
    )

    await state.set_state(ImageGenerationStates.waiting_results)

    try:
        file = await message.bot.get_file(source_file_id)
        image_io = await message.bot.download_file(file.file_path)
        source_image_data = image_io.read()

        try:
            await loading_msg.edit_text(
                "⏳ Редактирую изображение...\n\n"
                "<i>Этап 2/2: Генерирую новое изображение...</i>"
            )
        except TelegramBadRequest as e:
            logger.debug(f"Failed to update loading message: {e}")

        image_bytes = await ai_manager.edit_image(
            source_image_data=source_image_data,
            edit_request=edit_prompt,
            width=1024,
            height=1024,
        )

        try:
            await loading_msg.delete()
        except TelegramBadRequest as e:
            logger.debug(f"Failed to delete loading message: {e}")

        await state.update_data(
            last_edit_request=edit_prompt, last_source_file_id=source_file_id
        )

        caption = (
            "✅ <b>Готово! Изображение отредактировано.</b>\n\n"
            f"<i>Изменения:</i> {edit_prompt}"
        )
        photo_message = await message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="edited_image.jpg"),
            caption=caption,
        )
        result_file_id = (
            photo_message.photo[-1].file_id if photo_message.photo else None
        )
        await state.update_data(
            last_result_file_id=result_file_id,
            last_result_caption=caption,
        )

        await track_user_operation(user_id=message.from_user.id)

        return await message.answer(
            "Выберите действие:", reply_markup=image_generation_results_keyboard()
        )

    except Exception:
        try:
            await loading_msg.delete()
        except TelegramBadRequest as e:
            logger.debug(f"Failed to delete loading message: {e}")
        return await message.answer(
            "❌ Произошла ошибка при редактировании.\n\n"
            "<i>Попробуйте упростить запрос или начать заново.</i>",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(ImageGenerationStates.edit_prompt)
async def edit_prompt_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте текстовое описание изменений.",
        reply_markup=back_to_menu_keyboard(),
    )


# ============================================================================
# РЕЖИМ: СОЗДАНИЕ ПО ПРИМЕРУ
# ============================================================================


@router.message(ImageGenerationStates.upload_example, F.photo)
async def upload_example_photo_handler(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id

    await state.update_data(example_file_id=file_id)
    await state.set_state(ImageGenerationStates.example_prompt)

    return await message.answer(
        "✅ Пример загружен!\n\n"
        "Теперь опишите, что создать на основе этого примера.\n\n"
        "<i>Примеры:</i>\n"
        '• "Создай похожее изображение, но с детьми вместо взрослых"\n'
        '• "В таком же стиле нарисуй нашего волонтёра"\n'
        '• "Сделай логотип в таком же стиле, но с изображением дома"\n'
        '• "По примеру этой цветовой гаммы создай постер для мероприятия"',
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ImageGenerationStates.upload_example, F.document)
async def upload_example_document_handler(message: types.Message, state: FSMContext):
    document = message.document

    if not document.mime_type or not document.mime_type.startswith("image/"):
        return await message.answer(
            "Пожалуйста, загрузите изображение (фото или файл с изображением).",
            reply_markup=back_to_menu_keyboard(),
        )

    file_id = document.file_id

    await state.update_data(example_file_id=file_id)
    await state.set_state(ImageGenerationStates.example_prompt)

    return await message.answer(
        "✅ Пример загружен!\n\nТеперь опишите, что создать на основе этого примера.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ImageGenerationStates.upload_example)
async def upload_example_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте изображение-пример (фото или файл).",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ImageGenerationStates.example_prompt, F.text)
async def example_prompt_handler(message: types.Message, state: FSMContext):
    example_prompt = message.text.strip()

    if not example_prompt:
        return await message.answer(
            "Пожалуйста, опишите, что создать.", reply_markup=back_to_menu_keyboard()
        )

    data = await state.get_data()
    example_file_id = data.get("example_file_id")

    if not example_file_id:
        return await message.answer(
            "❌ Ошибка: пример не найден. Начните заново.",
            reply_markup=back_to_menu_keyboard(),
        )

    loading_msg = await message.answer(
        "⏳ Создаю изображение по примеру...\n\n"
        "<i>Этап 1/2: Анализирую стиль примера...</i>"
    )

    await state.set_state(ImageGenerationStates.waiting_results)

    try:
        file = await message.bot.get_file(example_file_id)
        image_io = await message.bot.download_file(file.file_path)
        example_image_data = image_io.read()

        try:
            await loading_msg.edit_text(
                "⏳ Создаю изображение по примеру...\n\n"
                "<i>Этап 2/2: Генерирую новое изображение...</i>"
            )
        except TelegramBadRequest as e:
            logger.debug(f"Failed to update loading message: {e}")

        image_bytes = await ai_manager.create_image_from_example(
            example_image_data=example_image_data,
            creation_request=example_prompt,
            width=1024,
            height=1024,
        )

        try:
            await loading_msg.delete()
        except TelegramBadRequest as e:
            logger.debug(f"Failed to delete loading message: {e}")

        await state.update_data(
            last_creation_request=example_prompt, last_example_file_id=example_file_id
        )

        caption = (
            "✅ <b>Готово! Изображение создано по примеру.</b>\n\n"
            f"<i>Описание:</i> {example_prompt}"
        )
        photo_message = await message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="example_based_image.jpg"),
            caption=caption,
        )
        result_file_id = (
            photo_message.photo[-1].file_id if photo_message.photo else None
        )
        await state.update_data(
            last_result_file_id=result_file_id,
            last_result_caption=caption,
        )

        await track_user_operation(user_id=message.from_user.id)

        return await message.answer(
            "Выберите действие:", reply_markup=image_generation_results_keyboard()
        )

    except Exception:
        try:
            await loading_msg.delete()
        except TelegramBadRequest as e:
            logger.debug(f"Failed to delete loading message: {e}")
        return await message.answer(
            "❌ Произошла ошибка.\n\n"
            "<i>Попробуйте упростить запрос или начать заново.</i>",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(ImageGenerationStates.example_prompt)
async def example_prompt_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте текстовое описание.",
        reply_markup=back_to_menu_keyboard(),
    )


# ============================================================================
# РЕЖИМ: СОЗДАНИЕ НОВОГО ИЗОБРАЖЕНИЯ
# ============================================================================


@router.message(ImageGenerationStates.description, F.text)
async def image_description_text_handler(message: types.Message, state: FSMContext):
    description = message.text.strip()

    if not description:
        return await message.answer(
            "Пожалуйста, отправьте описание картинки.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(description=description)
    await state.set_state(ImageGenerationStates.style)

    return await message.answer(
        "<b>Вопрос 2/3:</b> Какой стиль изображения?",
        reply_markup=image_style_keyboard(),
    )


@router.message(ImageGenerationStates.description)
async def image_description_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое описание.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("image_style:"))
async def image_style_handler(callback: types.CallbackQuery, state: FSMContext):
    style = callback.data.split(":")[1]

    style_names = {
        "realistic": "📸 Реалистичное фото",
        "illustration": "🎨 Иллюстрация/рисунок",
        "minimalism": "📱 Минимализм",
        "poster": "🎭 Постер/афиша",
        "business": "💼 Деловой стиль",
    }

    await state.update_data(style=style, style_name=style_names.get(style, style))
    await state.set_state(ImageGenerationStates.colors)
    await callback.answer()

    return await callback.message.edit_text(
        "<b>Вопрос 3/3:</b> Основные цвета:", reply_markup=image_colors_keyboard()
    )


@router.callback_query(F.data.startswith("image_colors:"))
async def image_colors_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler для выбора цветов и создания изображения"""
    colors = callback.data.split(":")[1]

    color_names = {
        "warm": "🔴 Тёплые (красный, оранжевый, жёлтый)",
        "cold": "🔵 Холодные (синий, голубой, зелёный)",
        "bright": "🌈 Яркие и контрастные",
        "neutral": "⚪ Нейтральные и пастельные",
        "auto": "💡 На ваш выбор (система сама подберёт)",
    }

    await state.update_data(colors=colors, colors_name=color_names.get(colors, colors))
    await state.set_state(ImageGenerationStates.overlay_mode)
    await callback.answer()

    return await callback.message.edit_text(
        "📝 <b>Хотите добавить текст на изображение?</b>\n\n"
        "Вы можете указать короткую фразу (для афиши, слогана или даты) и выбрать, где она появится.",
        reply_markup=overlay_mode_keyboard(),
    )


@router.callback_query(
    ImageGenerationStates.overlay_mode, F.data.startswith("overlay_mode:")
)
async def image_overlay_mode_handler(callback: types.CallbackQuery, state: FSMContext):
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
        return await _start_manual_image_generation(callback, state)

    await state.update_data(overlay_mode="custom")
    await state.set_state(ImageGenerationStates.overlay_text)

    return await callback.message.edit_text(
        "✍️ <b>Введите фразу</b>\n\n"
        "Например: «Участники — молодцы», «15 декабря 18:00», «Энергия добра».\n"
        "Фраза должна быть короткой и читаемой.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ImageGenerationStates.overlay_text, F.text)
async def image_overlay_text_handler(message: types.Message, state: FSMContext):
    text_value = message.text.strip()

    if not text_value:
        return await message.answer(
            "Пожалуйста, отправьте текст для подписи.",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(overlay_text=text_value)
    await state.set_state(ImageGenerationStates.overlay_position)

    return await message.answer(
        "📍 <b>Где разместить текст?</b>", reply_markup=overlay_position_keyboard()
    )


@router.message(ImageGenerationStates.overlay_text)
async def image_overlay_text_invalid(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте текстовую подпись.", reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(
    ImageGenerationStates.overlay_position, F.data.startswith("overlay_position:")
)
async def image_overlay_position_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    position = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(overlay_position=None if position == "auto" else position)
    await state.set_state(ImageGenerationStates.overlay_background)

    return await callback.message.edit_text(
        "🎨 <b>Выберите фон для текста</b>", reply_markup=overlay_background_keyboard()
    )


@router.callback_query(
    ImageGenerationStates.overlay_background, F.data.startswith("overlay_bg:")
)
async def image_overlay_background_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    background = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(
        overlay_background=None if background == "auto" else background
    )
    await state.set_state(ImageGenerationStates.overlay_font)

    font_options = _get_font_options()

    return await callback.message.edit_text(
        "🔠 <b>Выберите стиль шрифта</b>",
        reply_markup=overlay_font_keyboard(font_options),
    )


@router.callback_query(
    ImageGenerationStates.overlay_font, F.data.startswith("overlay_font:")
)
async def image_overlay_font_handler(callback: types.CallbackQuery, state: FSMContext):
    font_value = callback.data.split(":")[1]
    await callback.answer()

    await state.update_data(overlay_font=None if font_value == "random" else font_value)
    return await _start_manual_image_generation(callback, state)


# ============================================================================
# ОБРАБОТКА РЕЗУЛЬТАТОВ
# ============================================================================


@router.callback_query(F.data == "image_result:ok")
async def image_result_ok_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler для кнопки 'Всё отлично' после создания изображения"""
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Рад был помочь! 🎉")
    return await callback.message.answer(
        "👋 Главное меню", reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "image_result:regenerate")
@check_user_limit()
async def image_result_regenerate_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    data = await state.get_data()
    mode = data.get("mode")

    await callback.answer()
    loading_msg = await callback.message.answer("⏳ Создаю новый вариант...")

    try:
        if mode == "edit":
            edit_request = data.get("last_edit_request")
            source_file_id = data.get("last_source_file_id")

            if not edit_request or not source_file_id:
                await loading_msg.delete()
                return await callback.message.answer(
                    "❌ Не найдены данные для повтора",
                    reply_markup=image_generation_results_keyboard(),
                )

            file = await callback.bot.get_file(source_file_id)
            image_io = await callback.bot.download_file(file.file_path)
            source_image_data = image_io.read()

            image_bytes = await ai_manager.edit_image(
                source_image_data=source_image_data,
                edit_request=edit_request,
                width=1024,
                height=1024,
            )

        elif mode == "example":
            creation_request = data.get("last_creation_request")
            example_file_id = data.get("last_example_file_id")

            if not creation_request or not example_file_id:
                await loading_msg.delete()
                return await callback.message.answer(
                    "❌ Не найдены данные для повтора",
                    reply_markup=image_generation_results_keyboard(),
                )

            file = await callback.bot.get_file(example_file_id)
            image_io = await callback.bot.download_file(file.file_path)
            example_image_data = image_io.read()

            image_bytes = await ai_manager.create_image_from_example(
                example_image_data=example_image_data,
                creation_request=creation_request,
                width=1024,
                height=1024,
            )

        else:
            last_prompt = data.get("last_prompt")

            if not last_prompt:
                await loading_msg.delete()
                return await callback.message.answer(
                    "❌ Не найден предыдущий промпт",
                    reply_markup=image_generation_results_keyboard(),
                )

            overlay_text = data.get("last_overlay_text")
            overlay_font = data.get("last_overlay_font")
            overlay_position = data.get("last_overlay_position")
            overlay_background = data.get("last_overlay_background")
            overlay_config = _build_overlay_config(overlay_position, overlay_background)

            image_bytes = await ai_manager.generate_image(
                prompt=last_prompt,
                width=1024,
                height=1024,
                overlay_text=overlay_text,
                overlay_font=overlay_font,
                overlay_config=overlay_config,
            )

        await loading_msg.delete()

        caption = "✅ <b>Новый вариант готов!</b>"
        photo_message = await callback.message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="regenerated_image.jpg"),
            caption=caption,
        )
        result_file_id = (
            photo_message.photo[-1].file_id if photo_message.photo else None
        )
        await state.update_data(
            last_result_file_id=result_file_id,
            last_result_caption=caption,
        )

        await track_user_operation(user_id=callback.from_user.id)

        return await callback.message.answer(
            "Выберите действие:", reply_markup=image_generation_results_keyboard()
        )

    except Exception:
        await loading_msg.delete()
        return await callback.message.answer(
            "❌ Ошибка.\n\nПопробуйте позже",
            reply_markup=image_generation_results_keyboard(),
        )


@router.callback_query(
    ImageGenerationStates.waiting_results, F.data == "image_result:add_overlay"
)
async def image_result_add_overlay_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    data = await state.get_data()
    base_image_id = data.get("last_result_file_id")

    if not base_image_id:
        await callback.answer("Сначала создайте изображение", show_alert=True)
        return

    await state.set_state(ImageGenerationStates.adding_overlay)
    await state.update_data(
        pending_overlay_file_id=None,
        pending_overlay_type=None,
    )

    await callback.answer()
    return await callback.message.answer(
        "📎 Пришлите логотип или фото, которое нужно добавить к текущему изображению.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ImageGenerationStates.adding_overlay, F.photo | F.document)
async def image_overlay_file_handler(message: types.Message, state: FSMContext):
    file_id = _extract_image_file_id(message)

    if not file_id:
        return await message.answer(
            "Пожалуйста, отправьте изображение (фото или файл).",
            reply_markup=back_to_menu_keyboard(),
        )

    await state.update_data(pending_overlay_file_id=file_id)
    await state.set_state(ImageGenerationStates.adding_overlay_type)
    return await message.answer(
        "Выберите, как использовать изображение:",
        reply_markup=image_attachment_type_keyboard(),
    )


@router.message(ImageGenerationStates.adding_overlay)
async def image_overlay_file_invalid(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте изображение (фото или файл).",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(
    ImageGenerationStates.adding_overlay_type,
    F.data.startswith("image_asset:type:"),
)
async def image_overlay_type_handler(callback: types.CallbackQuery, state: FSMContext):
    _, _, value = callback.data.split(":")

    if value == "cancel":
        await state.set_state(ImageGenerationStates.waiting_results)
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await callback.answer("Добавление отменено")
        return await callback.message.answer(
            "Выберите действие:", reply_markup=image_generation_results_keyboard()
        )

    if value not in {"logo", "photo"}:
        await callback.answer("Используйте кнопки ниже", show_alert=True)
        return

    await state.update_data(pending_overlay_type=value)
    await state.set_state(ImageGenerationStates.adding_overlay_position)
    await callback.answer()
    return await callback.message.answer(
        "📍 Где разместить изображение?",
        reply_markup=image_attachment_position_keyboard(),
    )


@router.message(ImageGenerationStates.adding_overlay_type)
async def image_overlay_type_invalid(message: types.Message):
    return await message.answer(
        "Пожалуйста, выберите вариант с помощью кнопок.",
        reply_markup=image_attachment_type_keyboard(),
    )


@router.callback_query(
    ImageGenerationStates.adding_overlay_position,
    F.data.startswith("image_asset:pos:"),
)
async def image_asset_position_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    _, _, value = callback.data.split(":")

    if value == "cancel":
        await state.set_state(ImageGenerationStates.waiting_results)
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await callback.answer("Добавление отменено")
        return await callback.message.answer(
            "Выберите действие:", reply_markup=image_generation_results_keyboard()
        )

    data = await state.get_data()
    base_image_id = data.get("last_result_file_id")
    overlay_file_id = data.get("pending_overlay_file_id")
    overlay_type = data.get("pending_overlay_type")

    if not all([base_image_id, overlay_file_id, overlay_type]):
        await state.set_state(ImageGenerationStates.waiting_results)
        await state.update_data(
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await callback.answer("Изображение не найдено", show_alert=True)
        return await callback.message.answer(
            "❌ Не удалось подготовить изображение. Попробуйте ещё раз.",
            reply_markup=image_generation_results_keyboard(),
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

        caption = data.get("last_result_caption") or "✅ Обновлённое изображение"
        photo_message = await callback.message.answer_photo(
            photo=BufferedInputFile(merged_bytes, filename="image_with_overlay.png"),
            caption=caption,
        )
        result_file_id = (
            photo_message.photo[-1].file_id if photo_message.photo else base_image_id
        )

        await state.update_data(
            last_result_file_id=result_file_id,
            last_result_caption=caption,
            pending_overlay_file_id=None,
            pending_overlay_type=None,
        )
        await state.set_state(ImageGenerationStates.waiting_results)

        await track_user_operation(user_id=callback.from_user.id)

        return await callback.message.answer(
            "Выберите действие:", reply_markup=image_generation_results_keyboard()
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
        await state.set_state(ImageGenerationStates.waiting_results)

        return await callback.message.answer(
            "❌ Не удалось добавить изображение. Попробуйте другой файл.",
            reply_markup=image_generation_results_keyboard(),
        )


@router.message(ImageGenerationStates.adding_overlay_position)
async def image_asset_position_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, выберите позицию с помощью кнопок.",
        reply_markup=image_attachment_position_keyboard(),
    )


@router.callback_query(F.data == "image_result:edit")
async def image_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.mode_selection)
    await callback.answer()
    return await callback.message.answer(
        "🎨 <b>Генерация картинки</b>\n\nВыберите режим работы:",
        reply_markup=image_mode_keyboard(),
    )
