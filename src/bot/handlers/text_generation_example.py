from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import (
    back_to_menu_keyboard,
    main_menu_keyboard,
    from_example_generation_results_keyboard,
)
from src.bot.states import TextGenerationFromExampleStates, MainMenuStates
from src.services.ai_manager import ai_manager

router = Router()


@router.callback_query(F.data == "text_gen:example")
async def example_text_handler(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса генерации поста по примеру"""
    await state.set_state(TextGenerationFromExampleStates.example_post_input)
    await callback.answer()

    example_post = """📢 <b>Пример хорошего поста:</b>

💻🔥 IT-хакатон «Энергия добра» завершился!

Мы собрали более 300 участников со всей страны — всех объединила одна цель: придумать крутые решения для НКО и социальных проектов!

📌 Вот какие кейсы ребята разрабатывали:
➖ Телеграм-бот для ИИ-контента 🤖 — теперь НКО смогут легко создавать посты и привлекать больше внимания к своим проектам.
➖ Онлайн-навигатор по социальным инициативам Росатома 🏙️ — простой сайт с полезными ресурсами и проектами в каждом городе присутствия компании.
➖ Интерактивная карта для НКО 🗺️ — теперь можно быстро найти нужную организацию или узнать, где проходят ближайшие мероприятия.

💡 Присоединяйтесь к нам в следующем году и покажите свои таланты! 🌟

#itхакатон #энергиядобра #нко #социальныежелания #росатом"""

    return await callback.message.edit_text(
        "📝 <b>Генерация поста по примеру</b>\n\n"
        "Этот режим позволяет создать пост в стиле понравившегося вам примера.\n\n"
        "<b>Как это работает:</b>\n"
        "1️⃣ Вы пришлёте пример поста, который вам нравится\n"
        "2️⃣ Затем расскажете, о чём хотите написать\n"
        "3️⃣ Бот создаст новый пост в похожем стиле\n\n"
        f"{example_post}\n\n"
        "➡️ <b>Теперь пришлите ваш пример поста</b>\n"
        "Отправьте текст поста, стиль которого вам нравится.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationFromExampleStates.example_post_input, F.text)
async def example_post_input_handler(message: types.Message, state: FSMContext):
    """Получение примера поста от пользователя"""
    example_post = message.text.strip()

    if not example_post or len(example_post) < 50:
        return await message.answer(
            "❌ Пример поста слишком короткий.\n"
            "Пожалуйста, отправьте более подробный пример (минимум 50 символов).",
            reply_markup=back_to_menu_keyboard(),
        )

    # Сохраняем пример поста
    await state.update_data(example_post=example_post)
    await state.set_state(TextGenerationFromExampleStates.example_topic_input)

    return await message.answer(
        "✅ <b>Отлично! Пример получен.</b>\n\n"
        "Теперь расскажите, о чём вы хотите написать пост.\n\n"
        "Вы можете:\n"
        "• Написать текстом свою информацию\n"
        "• Отправить голосовое сообщение\n\n"
        "<i>💡 Опишите суть: о каком событии, акции или новости вы хотите рассказать, "
        "какие детали важно упомянуть (даты, цифры, участники).</i>",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationFromExampleStates.example_topic_input, F.text)
async def example_topic_text_handler(message: types.Message, state: FSMContext):
    """Получение новой темы текстом и генерация поста"""
    new_topic = message.text.strip()

    if not new_topic:
        return await message.answer(
            "Пожалуйста, опишите, о чём должен быть пост.",
            reply_markup=back_to_menu_keyboard(),
        )

    # Получаем сохранённый пример поста
    data = await state.get_data()
    example_post = data.get("example_post", "")

    if not example_post:
        return await message.answer(
            "❌ Не найден пример поста. Начните сначала.",
            reply_markup=back_to_menu_keyboard(),
        )

    user_id = message.from_user.id
    await state.set_state(TextGenerationFromExampleStates.waiting_results)

    return await generate_post_from_example(
        message, state, user_id, example_post, new_topic
    )


@router.message(TextGenerationFromExampleStates.example_topic_input, F.voice)
async def example_topic_voice_handler(message: types.Message, state: FSMContext):
    """Получение новой темы голосом и генерация поста"""
    transcribe_msg = await message.answer("⏳ Распознаю речь...")

    try:
        file = await message.bot.get_file(message.voice.file_id)
        audio_file = await message.bot.download_file(file.file_path)
        audio_data = audio_file.read()

        new_topic = await ai_manager.transcribe_voice(
            audio_data=audio_data, audio_format="opus"
        )

        await transcribe_msg.delete()

        if not new_topic or not new_topic.strip():
            return await message.answer(
                "Не удалось распознать речь. Попробуйте ещё раз.",
                reply_markup=back_to_menu_keyboard(),
            )

        await message.answer(f"📝 Вы сказали: {new_topic}")

        # Получаем сохранённый пример поста
        data = await state.get_data()
        example_post = data.get("example_post", "")

        if not example_post:
            return await message.answer(
                "❌ Не найден пример поста. Начните сначала.",
                reply_markup=back_to_menu_keyboard(),
            )

        user_id = message.from_user.id
        await state.set_state(TextGenerationFromExampleStates.waiting_results)

        return await generate_post_from_example(
            message, state, user_id, example_post, new_topic.strip()
        )

    except Exception:
        await transcribe_msg.delete()
        return await message.answer(
            "❌ Ошибка при распознавании речи. Попробуйте ещё раз позже",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(TextGenerationFromExampleStates.example_topic_input)
async def example_topic_invalid_handler(message: types.Message, state: FSMContext):
    """Обработка неправильного формата ввода темы"""
    return await message.answer(
        "Пожалуйста, отправьте текстовое или голосовое сообщение с описанием темы поста.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationFromExampleStates.example_post_input)
async def example_post_invalid_handler(message: types.Message, state: FSMContext):
    """Обработка неправильного формата ввода примера"""
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с примером поста.",
        reply_markup=back_to_menu_keyboard(),
    )


async def generate_post_from_example(
    message: types.Message,
    state: FSMContext,
    user_id: int,
    example_post: str,
    new_topic: str,
):
    """Генерация поста по примеру (только текст)"""
    loading_msg = await message.answer("⏳ Анализирую пример и создаю новый пост...")

    try:
        post = await ai_manager.generate_post_from_example(
            user_id=user_id,
            example_post=example_post,
            new_topic=new_topic,
        )

        await loading_msg.delete()

        await state.update_data(post=post, has_image=False)

        await message.answer("✨ <b>Готово! Ваш пост в стиле примера:</b>")
        await message.answer(f"{post}")

        return await message.answer(
            "Выберите действие", reply_markup=from_example_generation_results_keyboard()
        )

    except Exception:
        await loading_msg.delete()
        return await message.answer(
            "❌ Произошла ошибка. Попробуйте позже",
            reply_markup=back_to_menu_keyboard(),
        )


@router.callback_query(F.data == "example_result:ok")
async def text_result_ok_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer("Рад был помочь! 🎉")
    return await callback.message.answer(
        "👋 Главное меню", reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "example_result:edit")
async def text_result_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationFromExampleStates.editing)
    await callback.answer()
    return await callback.message.answer(
        "✏️ <b>Редактирование поста</b>\n\n"
        "Что нужно изменить в посте? Опишите ваши пожелания.",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(TextGenerationFromExampleStates.editing, F.text)
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
        updated_post = await ai_manager.edit_post(
            user_id=user_id,
            original_post=original_post,
            edit_request=edit_request,
        )

        await state.update_data(post=updated_post)
        await state.set_state(TextGenerationFromExampleStates.waiting_results)

        await message.answer("✨ <b>Пост обновлён:</b>")
        await message.answer(f"{updated_post}")

        return await message.answer(
            "Выберите действие", reply_markup=from_example_generation_results_keyboard()
        )

    except Exception:
        await loading_msg.delete()
        return await message.answer(
            "❌ Произошла ошибка при обновлении поста. Попробуйте ещё раз позже",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(TextGenerationFromExampleStates.editing)
async def editing_invalid_handler(message: types.Message, state: FSMContext):
    return await message.answer(
        "Пожалуйста, отправьте текстовое сообщение с описанием изменений.",
        reply_markup=back_to_menu_keyboard(),
    )
