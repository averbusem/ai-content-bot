from aiogram import types
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import main_menu_keyboard
from src.bot.states import MainMenuStates

router = Router()


@router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(MainMenuStates.main_menu)
    return await message.answer(
        "👋 Привет! Я помогу создать контент для вашей НКО",
        reply_markup=main_menu_keyboard()
    )
