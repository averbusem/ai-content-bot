from aiogram import Bot, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import main_menu_keyboard
from src.bot.states import MainMenuStates
from src.config import settings
from src.services.user import UserService

router = Router()


@router.message(CommandStart())
async def start_cmd(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
    is_admin: bool = False,
):
    await state.clear()

    user_service = UserService(
        session=session,
        bot=bot,
        admin_id=settings.ADMIN_ID,
    )

    from_user = message.from_user
    if from_user:
        await user_service.register_or_get_user(
            telegram_id=from_user.id,
            username=from_user.username,
        )

    if is_admin:
        await state.set_state(MainMenuStates.main_menu)
        return await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Для управления пользователями используйте команду /admin.\n"
            "А пока можете продолжить работу с основными функциями бота.",
            reply_markup=main_menu_keyboard(),
        )

    await state.set_state(MainMenuStates.main_menu)
    return await message.answer(
        "Привет! 👋\n\n"
        "Я помогу создать посты и картинки для социальных сетей вашей НКО.\n\n"
        "Выберите, что нужно сделать:",
        reply_markup=main_menu_keyboard(),
    )
