from aiogram import types
from aiogram import Router
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def start_cmd(message: types.Message):
    return await message.answer("👋 Привет! Я помогу создать контент для вашей НКО")
