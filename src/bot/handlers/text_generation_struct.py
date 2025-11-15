from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import back_to_menu_keyboard
from src.bot.states import TextGenerationStructStates

router = Router()


@router.callback_query(F.data == "text_gen:struct")
async def struct_form_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TextGenerationStructStates.method_selection)
    await callback.answer()
    return await callback.message.edit_text(
        "📋 Структурированная форма\n\n"
        "Эта функция будет реализована позже.",
        reply_markup=back_to_menu_keyboard()
    )

