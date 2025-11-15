from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import main_menu_keyboard, back_to_menu_keyboard, text_generation_method_keyboard
from src.bot.states import MainMenuStates, TextGenerationStates

router = Router()


@router.callback_query(F.data == "main_menu:back")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MainMenuStates.main_menu)
    await callback.answer()
    return await callback.message.edit_text(
        "👋 Главное меню",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "main_menu:text_generation")
async def text_generation_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStates.method_selection)
    await callback.answer()
    return await callback.message.edit_text(
        "📝 Генерация текста\n\n"
        "Выберите способ генерации:",
        reply_markup=text_generation_method_keyboard()
    )


@router.callback_query(F.data == "main_menu:text_editor")
async def text_editor_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "✏️ Редактор текста\n\n"
        "Реализация позже.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "main_menu:content_plan")
async def content_plan_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "📅 Контент-план\n\n"
        "Реализация позже.",
        reply_markup=back_to_menu_keyboard()
    )


