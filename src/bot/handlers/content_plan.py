from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import back_to_menu_keyboard, main_menu_keyboard
from src.services.ai_manager import AIManager
from src.bot.states import ContentPlanStates

router = Router()
ai_manager = AIManager()


@router.message(ContentPlanStates.duration_input, F.text)
async def duration_input_handler(message: types.Message, state: FSMContext):
    duration_text = message.text.strip()

    try:
        duration_days = int(duration_text)

        if duration_days < 1:
            return await message.answer(
                "❌ Количество дней должно быть больше 0.\nПопробуйте ещё раз:",
                reply_markup=back_to_menu_keyboard(),
            )

        if duration_days > 90:
            return await message.answer(
                "❌ Максимальный период - 90 дней.\nПопробуйте указать меньше:",
                reply_markup=back_to_menu_keyboard(),
            )

        await state.update_data(duration_days=duration_days)
        await state.set_state(ContentPlanStates.frequency_input)

        return await message.answer(
            f"✅ Период: {duration_days} дней\n\n"
            "Сколько постов в неделю планируете публиковать?\n"
            "Укажите число от 1 до 14 (например: 3, 5, 7)",
            reply_markup=back_to_menu_keyboard(),
        )

    except ValueError:
        return await message.answer(
            "❌ Пожалуйста, введите число (количество дней).\nНапример: 7, 14 или 30",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(ContentPlanStates.duration_input)
async def duration_invalid_handler(message: types.Message):
    return await message.answer(
        "❌ Пожалуйста, отправьте число (количество дней).\nНапример: 7, 14 или 30",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ContentPlanStates.frequency_input, F.text)
async def frequency_input_handler(message: types.Message, state: FSMContext):
    frequency_text = message.text.strip()

    try:
        posts_per_week = int(frequency_text)

        if posts_per_week < 1:
            return await message.answer(
                "❌ Количество постов должно быть больше 0.\nПопробуйте ещё раз:",
                reply_markup=back_to_menu_keyboard(),
            )

        if posts_per_week > 14:
            return await message.answer(
                "❌ Максимум 14 постов в неделю.\nПопробуйте указать меньше:",
                reply_markup=back_to_menu_keyboard(),
            )

        await state.update_data(posts_per_week=posts_per_week)
        await state.set_state(ContentPlanStates.preferences_input)

        return await message.answer(
            f"✅ Частота: {posts_per_week} постов в неделю\n\n"
            "Есть ли у вас предпочтения по темам или форматам?\n\n"
            "<i>Примеры:</i>\n"
            "• Контент для студентов и молодых специалистов\n"
            "• Программы стажировок, конкурсы, гранты\n"
            "• STEM-образование и популяризация науки\n"
            "• Истории успеха выпускников наших программ\n"
            "• Вовлекающий формат - вопросы, обсуждения, развенчание стереотипов о работе в атомной отрасли\n\n"
            'Или отправьте <b>"Нет"</b>, чтобы создать сбалансированный план.',
            reply_markup=back_to_menu_keyboard(),
        )

    except ValueError:
        return await message.answer(
            "❌ Пожалуйста, введите число (количество постов).\nНапример: 3, 5 или 7",
            reply_markup=back_to_menu_keyboard(),
        )


@router.message(ContentPlanStates.frequency_input)
async def frequency_invalid_handler(message: types.Message):
    return await message.answer(
        "❌ Пожалуйста, отправьте число (количество постов в неделю).\n"
        "Например: 3, 5 или 7",
        reply_markup=back_to_menu_keyboard(),
    )


@router.message(ContentPlanStates.preferences_input, F.text)
async def preferences_input_handler(message: types.Message, state: FSMContext):
    preferences_text = message.text.strip()

    preferences = (
        None
        if preferences_text.lower() in ["нет", "не нужно", "без предпочтений"]
        else preferences_text
    )

    await state.update_data(preferences=preferences)
    await state.set_state(ContentPlanStates.waiting_results)

    data = await state.get_data()
    duration_days = data.get("duration_days")
    posts_per_week = data.get("posts_per_week")
    user_id = message.from_user.id

    loading_msg = await message.answer("⏳ Создаю контент-план...\n")

    try:
        plan = await ai_manager.generate_content_plan(
            user_id=user_id,
            duration_days=duration_days,
            posts_per_week=posts_per_week,
            preferences=preferences,
        )

        await loading_msg.delete()

        await state.update_data(content_plan=plan)

        await message.answer(
            "✨ <b>Ваш контент-план готов!</b>\n\n"
            f"📅 Период: {duration_days} дней\n"
            f"📊 Частота: {posts_per_week} постов в неделю\n"
            + (f"💡 Предпочтения: {preferences}\n" if preferences else "")
        )

        await message.answer(f"<b>📋 КОНТЕНТ-ПЛАН:</b>\n\n{plan}")

        await state.clear()
        return await message.answer(
            "✅ Контент-план создан!\n\nВы можете сохранить его или создать новый.",
            reply_markup=main_menu_keyboard(),
        )

    except Exception as e:
        await loading_msg.delete()
        await state.clear()
        return await message.answer(
            f"❌ Произошла ошибка при создании контент-плана:\n"
            f"{str(e)}\n\n"
            "Попробуйте ещё раз позже.",
            reply_markup=main_menu_keyboard(),
        )


@router.message(ContentPlanStates.preferences_input)
async def preferences_invalid_handler(message: types.Message):
    return await message.answer(
        'Пожалуйста, опишите ваши предпочтения текстом\nили отправьте <b>"Нет"</b>.',
        reply_markup=back_to_menu_keyboard(),
    )
