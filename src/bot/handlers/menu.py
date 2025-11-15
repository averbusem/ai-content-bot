from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import main_menu_keyboard, back_to_menu_keyboard
from src.bot.states import MainMenuStates

router = Router()


@router.callback_query(F.data == "menu:main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(MainMenuStates.main)
    await callback.answer()
    return await callback.message.edit_text(
        "👋 Главное меню",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "menu:text_generation")
async def text_generation_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "📝 Генерация текста\n\n"
        "Эта функция будет реализована позже.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "menu:image_generation")
async def image_generation_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "🎨 Генерация картинки\n\n"
        "Эта функция будет реализована позже.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "menu:text_editor")
async def text_editor_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "✏️ Редактор текста\n\n"
        "Реализация позже.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "menu:content_plan")
async def content_plan_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "📅 Контент-план\n\n"
        "Реализация позже.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "menu:nko_data")
async def nko_data_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "⚙️ Рассказать об НКО\n\n"
        "Эта функция будет реализована позже.",
        reply_markup=back_to_menu_keyboard()
    )


@router.callback_query(F.data == "menu:help")
async def help_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    return await callback.message.edit_text(
        "❓ Помощь\n\n"
        "Эта функция будет реализована позже.",
        reply_markup=back_to_menu_keyboard()
    )

