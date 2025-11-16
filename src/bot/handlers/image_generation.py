from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

from src.bot.keyboards import (
    back_to_menu_keyboard,
    image_style_keyboard,
    image_colors_keyboard,
    image_generation_results_keyboard,
    main_menu_keyboard,
    image_mode_keyboard
)
from src.bot.states import ImageGenerationStates, MainMenuStates
from src.services.ai_manager import AIManager
router = Router()
ai_manager = AIManager()


@router.callback_query(F.data == "main_menu:image_generation")
async def image_generation_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.mode_selection)
    await callback.answer()
    return await callback.message.edit_text(
        "🎨 <b>Генерация картинки</b>\n\n"
        "Выберите режим работы:",
        reply_markup=image_mode_keyboard()
    )


@router.callback_query(F.data == "image_mode:create")
async def image_mode_create_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.description)
    await state.update_data(mode="create", uploaded_files=[])
    await callback.answer()
    return await callback.message.edit_text(
        "🎨 <b>Создание нового изображения</b>\n\n"
        "<b>Вопрос 1/3:</b> Опишите, какую картинку нужно создать.\n\n"
        "<i>💡 Чем подробнее описание, тем лучше результат!</i>\n\n"
        "<i>Примеры хороших описаний:</i>\n"
        "• \"Волонтёры убирают мусор на берегу озера, собирают его в мешки. "
        "На заднем плане озеро и деревья, солнечная погода.\"\n"
        "• \"Дети читают книги в библиотеке, уютная атмосфера, тёплый свет\"\n"
        "• \"Логотип благотворительного фонда с изображением дома и сердца\"",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "image_mode:edit")
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
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "image_mode:example")
async def image_mode_example_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.upload_example)
    await state.update_data(mode="example", uploaded_files=[])
    await callback.answer()
    return await callback.message.edit_text(
        "📋 <b>Создание по примеру</b>\n\n"
        "Загрузите изображение-пример.\n\n"
        "<i>Я создам новое изображение в похожем стиле, с похожей композицией или цветовой гаммой.</i>",
        reply_markup=back_to_menu_keyboard()
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
        "• \"Сделай фон более ярким\"\n"
        "• \"Убери человека слева\"\n"
        "• \"Добавь текст 'Спасибо волонтёрам'\"\n"
        "• \"Измени стиль на акварельный\"\n"
        "• \"Улучши качество и детализацию\"",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(ImageGenerationStates.upload_for_edit, F.document)
async def upload_for_edit_document_handler(message: types.Message, state: FSMContext):
    document = message.document

    if not document.mime_type or not document.mime_type.startswith("image/"):
        return await message.answer(
            "Пожалуйста, загрузите изображение (фото или файл с изображением).",
            reply_markup=back_to_menu_keyboard()
        )

    file_id = document.file_id

    await state.update_data(source_file_id=file_id)
    await state.set_state(ImageGenerationStates.edit_prompt)

    return await message.answer(
        "✅ Изображение загружено!\n\n"
        "Теперь опишите, что нужно изменить.",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(ImageGenerationStates.upload_for_edit)
async def upload_for_edit_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте изображение (фото или файл).",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(ImageGenerationStates.edit_prompt, F.text)
async def edit_prompt_handler(message: types.Message, state: FSMContext):
    edit_prompt = message.text.strip()

    if not edit_prompt:
        return await message.answer(
            "Пожалуйста, опишите, что нужно изменить.",
            reply_markup=back_to_menu_keyboard()
        )

    data = await state.get_data()
    source_file_id = data.get("source_file_id")

    if not source_file_id:
        return await message.answer(
            "❌ Ошибка: изображение не найдено. Начните заново.",
            reply_markup=back_to_menu_keyboard()
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
        except:
            pass

        image_bytes = await ai_manager.edit_image(
            source_image_data=source_image_data,
            edit_request=edit_prompt,
            width=1024,
            height=1024
        )

        try:
            await loading_msg.delete()
        except Exception:
            pass

        await state.update_data(
            last_edit_request=edit_prompt,
            last_source_file_id=source_file_id
        )

        await message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="edited_image.jpg"),
            caption=f"✅ <b>Готово! Изображение отредактировано.</b>\n\n"
                    f"<i>Изменения:</i> {edit_prompt}"
        )

        return await message.answer(
            "Выберите действие:",
            reply_markup=image_generation_results_keyboard()
        )

    except Exception as e:
        try:
            await loading_msg.delete()
        except Exception:
            pass
        return await message.answer(
            f"❌ Произошла ошибка при редактировании.\n\n"
            f"<i>Попробуйте упростить запрос или начать заново.</i>",
            reply_markup=back_to_menu_keyboard()
        )


@router.message(ImageGenerationStates.edit_prompt)
async def edit_prompt_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте текстовое описание изменений.",
        reply_markup=back_to_menu_keyboard()
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
        "• \"Создай похожее изображение, но с детьми вместо взрослых\"\n"
        "• \"В таком же стиле нарисуй нашего волонтёра\"\n"
        "• \"Сделай логотип в таком же стиле, но с изображением дома\"\n"
        "• \"По примеру этой цветовой гаммы создай постер для мероприятия\"",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(ImageGenerationStates.upload_example, F.document)
async def upload_example_document_handler(message: types.Message, state: FSMContext):
    document = message.document

    if not document.mime_type or not document.mime_type.startswith("image/"):
        return await message.answer(
            "Пожалуйста, загрузите изображение (фото или файл с изображением).",
            reply_markup=back_to_menu_keyboard()
        )

    file_id = document.file_id

    await state.update_data(example_file_id=file_id)
    await state.set_state(ImageGenerationStates.example_prompt)

    return await message.answer(
        "✅ Пример загружен!\n\n"
        "Теперь опишите, что создать на основе этого примера.",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(ImageGenerationStates.upload_example)
async def upload_example_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте изображение-пример (фото или файл).",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(ImageGenerationStates.example_prompt, F.text)
async def example_prompt_handler(message: types.Message, state: FSMContext):
    example_prompt = message.text.strip()

    if not example_prompt:
        return await message.answer(
            "Пожалуйста, опишите, что создать.",
            reply_markup=back_to_menu_keyboard()
        )

    data = await state.get_data()
    example_file_id = data.get("example_file_id")

    if not example_file_id:
        return await message.answer(
            "❌ Ошибка: пример не найден. Начните заново.",
            reply_markup=back_to_menu_keyboard()
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
        except:
            pass

        image_bytes = await ai_manager.create_image_from_example(
            example_image_data=example_image_data,
            creation_request=example_prompt,
            width=1024,
            height=1024
        )

        try:
            await loading_msg.delete()
        except Exception:
            pass

        await state.update_data(
            last_creation_request=example_prompt,
            last_example_file_id=example_file_id
        )

        await message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="example_based_image.jpg"),
            caption=f"✅ <b>Готово! Изображение создано по примеру.</b>\n\n"
                    f"<i>Описание:</i> {example_prompt}"
        )

        return await message.answer(
            "Выберите действие:",
            reply_markup=image_generation_results_keyboard()
        )

    except Exception as e:
        try:
            await loading_msg.delete()
        except Exception:
            pass
        return await message.answer(
            f"❌ Произошла ошибка.\n\n"
            f"<i>Попробуйте упростить запрос или начать заново.</i>",
            reply_markup=back_to_menu_keyboard()
        )


@router.message(ImageGenerationStates.example_prompt)
async def example_prompt_invalid_handler(message: types.Message):
    return await message.answer(
        "Пожалуйста, отправьте текстовое описание.",
        reply_markup=back_to_menu_keyboard()
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
            reply_markup=back_to_menu_keyboard()
        )

    await state.update_data(description=description)
    await state.set_state(ImageGenerationStates.style)

    return await message.answer(
        "<b>Вопрос 2/3:</b> Какой стиль изображения?",
        reply_markup=image_style_keyboard()
    )


@router.message(ImageGenerationStates.description)
async def image_description_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое описание.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data.startswith("image_style:"))
async def image_style_handler(callback: types.CallbackQuery, state: FSMContext):
    style = callback.data.split(":")[1]

    style_names = {
        "realistic": "📸 Реалистичное фото",
        "illustration": "🎨 Иллюстрация/рисунок",
        "minimalism": "📱 Минимализм",
        "poster": "🎭 Постер/афиша",
        "business": "💼 Деловой стиль"
    }

    await state.update_data(style=style, style_name=style_names.get(style, style))
    await state.set_state(ImageGenerationStates.colors)
    await callback.answer()

    return await callback.message.edit_text(
        "<b>Вопрос 3/3:</b> Основные цвета:",
        reply_markup=image_colors_keyboard()
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
        "auto": "💡 На ваш выбор (система сама подберёт)"
    }

    await state.update_data(colors=colors, colors_name=color_names.get(colors, colors))
    await callback.answer()

    data = await state.get_data()
    description = data.get("description", "")
    style = data.get("style", "")
    style_name = data.get("style_name", "")
    colors_name = data.get("colors_name", "")

    if not description:
        return await callback.message.edit_text(
            "❌ Ошибка: не указано описание изображения. Пожалуйста, начните заново.",
            reply_markup=back_to_menu_keyboard()
        )
    
    # Показываем сообщение о создании
    loading_msg = await callback.message.edit_text(
        "⏳ Создаю изображение...\n\n"
        f"<b>Описание:</b> {description}\n"
        f"<b>Стиль:</b> {style_name}\n"
        f"<b>Цвета:</b> {colors_name}"
    )

    await state.set_state(ImageGenerationStates.waiting_results)

    try:
        style_prompts = {
            "realistic": "реалистичная фотография, высокая детализация",
            "illustration": "художественная иллюстрация, рисунок",
            "minimalism": "минималистичный стиль, простота, чистые линии",
            "poster": "стиль постера или афиши, яркий, привлекающий внимание",
            "business": "деловой стиль, профессиональный вид"
        }

        color_prompts = {
            "warm": "тёплые цвета (красный, оранжевый, жёлтый)",
            "cold": "холодные цвета (синий, голубой, зелёный)",
            "bright": "яркие и контрастные цвета",
            "neutral": "нейтральные и пастельные тона",
            "auto": ""
        }

        style_desc = style_prompts.get(style, "")
        color_desc = color_prompts.get(colors, "")

        full_prompt = f"{description}. {style_desc}"
        if color_desc:
            full_prompt += f". {color_desc}"

        image_bytes = await ai_manager.generate_image(
            prompt=full_prompt,
            width=1024,
            height=1024
        )

        try:
            await loading_msg.delete()
        except Exception:
            pass

        await state.update_data(last_prompt=full_prompt)

        await callback.message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="generated_image.jpg"),
            caption="✅ <b>Готово! Вот ваше изображение.</b>"
        )

        return await callback.message.answer(
            "Выберите действие:",
            reply_markup=image_generation_results_keyboard()
        )

    except Exception as e:
        try:
            await loading_msg.delete()
        except Exception:
            pass
        return await callback.message.answer(
            f"❌ Произошла ошибка при генерации изображения\n\n"
            "Попробуйте ещё раз или вернитесь в главное меню.",
            reply_markup=back_to_menu_keyboard()
        )


# ============================================================================
# ОБРАБОТКА РЕЗУЛЬТАТОВ
# ============================================================================

@router.callback_query(F.data == "image_result:ok")
async def image_result_ok_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler для кнопки 'Всё отлично' после создания изображения"""
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Рад был помочь! 🎉")
    return await callback.message.answer(
        "👋 Главное меню",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "image_result:regenerate")
async def image_result_regenerate_handler(callback: types.CallbackQuery, state: FSMContext):
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
                    reply_markup=image_generation_results_keyboard()
                )

            file = await callback.bot.get_file(source_file_id)
            image_io = await callback.bot.download_file(file.file_path)
            source_image_data = image_io.read()

            image_bytes = await ai_manager.edit_image(
                source_image_data=source_image_data,
                edit_request=edit_request,
                width=1024,
                height=1024
            )

        elif mode == "example":
            creation_request = data.get("last_creation_request")
            example_file_id = data.get("last_example_file_id")

            if not creation_request or not example_file_id:
                await loading_msg.delete()
                return await callback.message.answer(
                    "❌ Не найдены данные для повтора",
                    reply_markup=image_generation_results_keyboard()
                )

            file = await callback.bot.get_file(example_file_id)
            image_io = await callback.bot.download_file(file.file_path)
            example_image_data = image_io.read()

            image_bytes = await ai_manager.create_image_from_example(
                example_image_data=example_image_data,
                creation_request=creation_request,
                width=1024,
                height=1024
            )

        else:
            last_prompt = data.get("last_prompt")

            if not last_prompt:
                await loading_msg.delete()
                return await callback.message.answer(
                    "❌ Не найден предыдущий промпт",
                    reply_markup=image_generation_results_keyboard()
                )

            image_bytes = await ai_manager.generate_image(
                prompt=last_prompt,
                width=1024,
                height=1024
            )

        await loading_msg.delete()

        await callback.message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="regenerated_image.jpg"),
            caption="✅ <b>Новый вариант готов!</b>"
        )

        return await callback.message.answer(
            "Выберите действие:",
            reply_markup=image_generation_results_keyboard()
        )

    except Exception as e:
        await loading_msg.delete()
        return await callback.message.answer(
            f"❌ Ошибка.\n\n"
            f"Попробуйте позже",
            reply_markup=image_generation_results_keyboard()
        )

@router.callback_query(F.data == "image_result:edit")
async def image_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ImageGenerationStates.mode_selection)
    await callback.answer()
    return await callback.message.answer(
        "🎨 <b>Генерация картинки</b>\n\n"
        "Выберите режим работы:",
        reply_markup=image_mode_keyboard()
    )
