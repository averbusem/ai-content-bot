from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.bot_decorators import check_user_limit
from src.bot.keyboards import (
    back_to_menu_keyboard,
    main_menu_keyboard,
    text_generation_method_keyboard,
    post_schedule_main_keyboard,
)
from src.bot.states import (
    ContentPlanStates,
    MainMenuStates,
    PostScheduleStates,
    TextGenerationStates,
    TextEditorStates,
)

router = Router()


@router.callback_query(F.data == "main_menu:back")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer()
    return await callback.message.edit_text(
        "🏠 Главное меню\n\nВыберите действие из списка ниже:",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "main_menu:text_generation")
async def text_generation_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStates.method_selection)
    await callback.answer()
    return await callback.message.edit_text(
        "📝 Создание поста\n\nВыберите способ создания:",
        reply_markup=text_generation_method_keyboard(),
    )


@router.callback_query(F.data == "main_menu:text_editor")
@check_user_limit()
async def text_editor_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(TextEditorStates.original_text)
    return await callback.message.edit_text(
        "✏️ Редактор текста\n\nПришлите Ваш пост и мы исправим все ошибки!",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "main_menu:content_plan")
@check_user_limit()
async def content_plan_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ContentPlanStates.duration_input)
    await callback.answer()
    return await callback.message.edit_text(
        "📅 <b>Создание контент-плана</b>\n\n"
        "Контент-план поможет вам регулярно публиковать разнообразный контент.\n\n"
        "На какой период создать план?\n"
        "Укажите количество дней (например: 7, 14, 30)",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "main_menu:schedule_post")
async def schedule_post_start(callback: types.CallbackQuery, state: FSMContext):
    """
    Переход в меню планирования поста из главного меню.

    Дальнейший флоу обрабатывается в модуле handlers.post_schedule.
    """
    await state.set_state(PostScheduleStates.mode_selection)
    await callback.answer()
    return await callback.message.edit_text(
        "📆 <b>Планирование поста</b>\n\n"
        "Выберите режим планирования: напоминание или автопубликация.",
        reply_markup=post_schedule_main_keyboard(),
    )
