from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import (
    main_menu_keyboard,
    back_to_menu_keyboard,
    text_generation_method_keyboard,
)
from src.bot.states import (
    MainMenuStates,
    TextGenerationStates,
    TextEditorStates,
    ContentPlanStates,
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
async def text_editor_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(TextEditorStates.original_text)
    return await callback.message.edit_text(
        "✏️ Редактор текста\n\nПришлите Ваш пост и мы исправим все ошибки!",
        reply_markup=back_to_menu_keyboard(),
    )


@router.callback_query(F.data == "main_menu:content_plan")
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
