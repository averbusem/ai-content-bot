from aiogram import types
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import main_menu_keyboard
from src.bot.states import MainMenuStates

router = Router()


@router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(MainMenuStates.main_menu)
    return await message.answer(
        "Привет! 👋\n\n"
        "Я помогу создать посты и картинки для социальных сетей вашей НКО.\n\n"
        "Выберите, что нужно сделать:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("use"))
async def use_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(MainMenuStates.main_menu)
    return await message.answer(
        "Привет! 👋\n\n"
        "Я помогу создать посты и картинки для социальных сетей вашей НКО.\n\n"
        "Выберите, что нужно сделать:",
        reply_markup=main_menu_keyboard(),
    )
