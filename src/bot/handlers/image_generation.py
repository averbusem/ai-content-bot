from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import (
    back_to_menu_keyboard, 
    image_style_keyboard, 
    image_colors_keyboard,
    image_generation_results_keyboard,
    main_menu_keyboard
)
from src.bot.states import ImageGenerationStates, MainMenuStates
from src.services.ai_manager import AIManager

router = Router()
ai_manager = AIManager()


@router.callback_query(F.data == "main_menu:image_generation")
async def image_generation_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler для кнопки '🎨 Генерация картинки' из главного меню"""
    await state.set_state(ImageGenerationStates.description)
    await callback.answer()
    return await callback.message.edit_text(
        "🎨 <b>Генерация картинки</b>\n\n"
        "Я создам изображение через нейросеть по вашему описанию.\n\n"
        "<b>Вопрос 1/3:</b> Опишите, какую картинку нужно создать, или загрузите свои файлы для обработки.\n\n"
        "<i>💡 Чем подробнее описание, тем лучше результат!</i>\n\n"
        "<i>Пример хорошего описания:</i>\n"
        "\"Волонтёры убирают мусор на берегу озера, собирают его в мешки. "
        "На заднем плане озеро и деревья, солнечная погода.\"\n\n"
        "<i>Или загрузите:</i>\n"
        "• Логотип вашей НКО\n"
        "• Фотографии для коллажа\n"
        "• Любые изображения для обработки",
        reply_markup=back_to_menu_keyboard()
    )


@router.message(ImageGenerationStates.description, F.text)
async def image_description_text_handler(message: types.Message, state: FSMContext):
    """Handler для текстового описания картинки"""
    description = message.text.strip()
    
    if not description:
        return await message.answer(
            "Пожалуйста, отправьте описание картинки или загрузите изображение.",
            reply_markup=back_to_menu_keyboard()
        )
    
    data = await state.get_data()
    uploaded_files = data.get("uploaded_files", [])
    
    await state.update_data(description=description, uploaded_files=uploaded_files)
    await state.set_state(ImageGenerationStates.style)
    
    return await message.answer(
        "<b>Вопрос 2/3:</b> Какой стиль изображения?",
        reply_markup=image_style_keyboard()
    )


@router.message(ImageGenerationStates.description, F.photo)
async def image_description_photo_handler(message: types.Message, state: FSMContext):
    """Handler для загрузки фотографий"""
    photo = message.photo[-1]  # Берем фото наибольшего размера
    file_id = photo.file_id
    
    data = await state.get_data()
    uploaded_files = data.get("uploaded_files", [])
    uploaded_files.append({"type": "photo", "file_id": file_id})
    
    description = message.caption.strip() if message.caption else ""
    
    await state.update_data(
        description=description,
        uploaded_files=uploaded_files
    )
    
    if not description:
        return await message.answer(
            "Фото загружено! Теперь опишите, что нужно сделать с изображением, или загрузите ещё файлы.\n\n"
            "Если всё готово, отправьте любое текстовое сообщение (например, \"готово\") для продолжения.",
            reply_markup=back_to_menu_keyboard()
        )
    
    await state.set_state(ImageGenerationStates.style)
    return await message.answer(
        "<b>Вопрос 2/3:</b> Какой стиль изображения?",
        reply_markup=image_style_keyboard()
    )


@router.message(ImageGenerationStates.description, F.document)
async def image_description_document_handler(message: types.Message, state: FSMContext):
    """Handler для загрузки документов (изображений)"""
    document = message.document
    
    if not document.mime_type or not document.mime_type.startswith("image/"):
        return await message.answer(
            "Пожалуйста, загрузите изображение (фото или файл с изображением).",
            reply_markup=back_to_menu_keyboard()
        )
    
    file_id = document.file_id
    
    data = await state.get_data()
    uploaded_files = data.get("uploaded_files", [])
    uploaded_files.append({"type": "document", "file_id": file_id})
    
    description = message.caption.strip() if message.caption else ""
    
    await state.update_data(
        description=description,
        uploaded_files=uploaded_files
    )
    
    if not description:
        return await message.answer(
            "Изображение загружено! Теперь опишите, что нужно сделать с изображением, или загрузите ещё файлы.\n\n"
            "Если всё готово, отправьте любое текстовое сообщение (например, \"готово\") для продолжения.",
            reply_markup=back_to_menu_keyboard()
        )
    
    await state.set_state(ImageGenerationStates.style)
    return await message.answer(
        "<b>Вопрос 2/3:</b> Какой стиль изображения?",
        reply_markup=image_style_keyboard()
    )


@router.message(ImageGenerationStates.description)
async def image_description_invalid_handler(message: types.Message, state: FSMContext):
    """Handler для невалидного ввода в состоянии описания"""
    return await message.answer(
        "Пожалуйста, отправьте текстовое описание или загрузите изображение (фото или файл).",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data.startswith("image_style:"))
async def image_style_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler для выбора стиля изображения"""
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
    """Handler для выбора цветов и генерации изображения"""
    colors = callback.data.split(":")[1]
    
    color_names = {
        "warm": "🔴 Тёплые (красный, оранжевый, жёлтый)",
        "cold": "🔵 Холодные (синий, голубой, зелёный)",
        "bright": "🌈 Яркие и контрастные",
        "neutral": "⚪ Нейтральные и пастельные",
        "auto": "💡 На ваш выбор (ИИ сам подберёт)"
    }
    
    await state.update_data(colors=colors, colors_name=color_names.get(colors, colors))
    await callback.answer()
    
    data = await state.get_data()
    description = data.get("description", "")
    style = data.get("style", "")
    style_name = data.get("style_name", "")
    colors_name = data.get("colors_name", "")
    
    # Проверяем, что есть описание
    if not description:
        return await callback.message.edit_text(
            "❌ Ошибка: не указано описание изображения. Пожалуйста, начните заново.",
            reply_markup=back_to_menu_keyboard()
        )
    
    # Показываем сообщение о генерации
    loading_msg = await callback.message.edit_text(
        "⏳ Генерирую изображение...\n\n"
        f"<b>Описание:</b> {description}\n"
        f"<b>Стиль:</b> {style_name}\n"
        f"<b>Цвета:</b> {colors_name}"
    )
    
    await state.set_state(ImageGenerationStates.waiting_results)
    
    try:
        # Генерируем изображение
        image_bytes = await ai_manager.generate_image_from_params(
            description=description,
            style=style,
            colors=colors,
            width=1024,
            height=1024
        )
        
        # Сохраняем параметры для возможного редактирования
        prompt = ai_manager.image_generator.build_image_prompt(description, style, colors)
        await state.update_data(
            image_prompt=prompt
        )
        
        # Отправляем изображение
        await callback.message.answer_photo(
            photo=types.BufferedInputFile(
                file=image_bytes,
                filename="generated_image.png"
            ),
            caption="✅ <b>Готово! Вот ваше изображение.</b>"
        )
        
        # Удаляем сообщение о загрузке и отправляем клавиатуру
        await loading_msg.delete()
        return await callback.message.answer(
            "Выберите действие:",
            reply_markup=image_generation_results_keyboard()
        )
        
    except Exception as e:
        await loading_msg.delete()
        return await callback.message.answer(
            f"❌ Произошла ошибка при генерации изображения: {str(e)}\n\n"
            "Попробуйте ещё раз или вернитесь в главное меню.",
            reply_markup=back_to_menu_keyboard()
        )


@router.callback_query(F.data == "image_result:ok")
async def image_result_ok_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler для кнопки 'Всё отлично' после генерации изображения"""
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Рад был помочь! 🎉")
    return await callback.message.edit_text(
        "👋 Главное меню",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "image_result:edit")
async def image_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    """Handler для кнопки 'Изменить' после генерации изображения"""
    await state.set_state(ImageGenerationStates.description)
    await callback.answer()
    return await callback.message.edit_text(
        "🎨 <b>Генерация картинки</b>\n\n"
        "Я создам изображение через нейросеть по вашему описанию.\n\n"
        "<b>Вопрос 1/3:</b> Опишите, какую картинку нужно создать, или загрузите свои файлы для обработки.\n\n"
        "<i>Примеры описаний:</i>\n"
        "• \"Волонтёры раздают новогодние подарки детям\"\n"
        "• \"Логотип фонда на фоне города\"\n"
        "• \"Счастливая собака в приюте\"\n"
        "• \"Афиша для мероприятия с датой 20 декабря\"\n\n"
        "<i>Или загрузите:</i>\n"
        "• Логотип вашей НКО\n"
        "• Фотографии для коллажа\n"
        "• Любые изображения для обработки",
        reply_markup=back_to_menu_keyboard()
    )

