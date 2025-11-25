from typing import Optional

from aiogram import Bot, F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import (
    admin_back_to_main_keyboard,
    admin_user_management_keyboard,
    main_menu_keyboard,
)
from src.bot.states import AdminMenuStates
from src.config import settings
from src.db.models import User
from src.services.user import UserService

router = Router()

USER_GREETING = (
    "Привет! 👋\n\n"
    "Я помогу создать посты и картинки для социальных сетей вашей НКО.\n\n"
    "Выберите, что нужно сделать:"
)


async def _check_admin(callback_or_message, is_admin: bool) -> bool:
    if is_admin:
        return True
    if isinstance(callback_or_message, types.CallbackQuery):
        await callback_or_message.answer(
            "Доступ к административным действиям запрещён.",
            show_alert=True,
        )
    else:
        await callback_or_message.answer("Доступ запрещён.")
    return False


def _format_user_line(user: User) -> str:
    username = user.username or "без username"
    return f"{user.telegram_id} — {username}"


def _split_identifier(value: str) -> tuple[Optional[int], Optional[str]]:
    normalized = value.strip()
    if normalized.startswith("@"):
        normalized = normalized[1:]

    if not normalized:
        return None, None

    try:
        return int(normalized), None
    except ValueError:
        return None, normalized


@router.message(Command("admin"))
async def admin_menu_command_handler(
    message: types.Message,
    state: FSMContext,
    is_admin: bool = False,
):
    if not await _check_admin(message, is_admin):
        return None

    await state.set_state(AdminMenuStates.user_management)
    return await message.answer(
        "👤 Управление пользователями\n\nВыберите действие:",
        reply_markup=admin_user_management_keyboard(),
    )


@router.callback_query(F.data == "admin_menu:back")
async def admin_back_to_main_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    is_admin: bool = False,
):
    if not await _check_admin(callback, is_admin):
        return None

    await state.set_state(AdminMenuStates.user_management)
    await callback.answer()
    return await callback.message.edit_text(
        "👤 Управление пользователями\n\nВыберите действие:",
        reply_markup=admin_user_management_keyboard(),
    )


@router.callback_query(F.data == "admin_menu:requests")
async def list_pending_requests_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
    is_admin: bool = False,
):
    if not await _check_admin(callback, is_admin):
        return None

    user_service = UserService(session=session, bot=bot, admin_id=settings.ADMIN_ID)
    pending_users = await user_service.list_pending_users()

    if pending_users:
        lines = "\n".join(_format_user_line(user) for user in pending_users)
        text = (
            "📋 Заявки на доступ:\n\n"
            f"{lines}\n\n"
            "Напишите айди пользователя, кому вы разрешаете доступ к боту."
        )
    else:
        text = (
            "✅ На данный момент заявок нет.\n\n"
            "Как только появится новый запрос, бот уведомит вас."
        )

    await state.set_state(AdminMenuStates.approve_user)
    await callback.answer()
    return await callback.message.edit_text(
        text,
        reply_markup=admin_back_to_main_keyboard(),
    )


@router.message(AdminMenuStates.approve_user)
async def approve_user_by_message_handler(
    message: types.Message,
    session: AsyncSession,
    bot: Bot,
    is_admin: bool = False,
):
    if not await _check_admin(message, is_admin):
        return

    user_service = UserService(session=session, bot=bot, admin_id=settings.ADMIN_ID)
    raw_value = message.text or ""
    telegram_id, username = _split_identifier(raw_value)

    if telegram_id is None and username is None:
        return await message.answer(
            "⚠️ Укажите ID или username пользователя.\nПример: 123456 или @username.",
            reply_markup=admin_back_to_main_keyboard(),
        )

    if telegram_id is not None:
        user = await user_service.activate_user(telegram_id=telegram_id)
    else:
        user = await user_service.activate_user_by_username(username=username or "")

    if user is None:
        text = "Пользователь не найден. Проверьте ID или username."
    else:
        text = f"✅ Доступ пользователю {user.telegram_id} предоставлен."
        await bot.send_message(
            chat_id=user.telegram_id,
            text=USER_GREETING,
            reply_markup=main_menu_keyboard(),
        )

    return await message.answer(
        f"{text}\n\nОтправьте следующий ID или вернитесь в главное меню.",
        reply_markup=admin_back_to_main_keyboard(),
    )


@router.callback_query(F.data == "admin_menu:block")
async def start_block_user_flow_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    is_admin: bool = False,
):
    if not await _check_admin(callback, is_admin):
        return None

    await state.set_state(AdminMenuStates.block_user)
    await callback.answer()
    return await callback.message.edit_text(
        "⛔ Введите ID или username пользователя, которого нужно заблокировать.",
        reply_markup=admin_back_to_main_keyboard(),
    )


@router.message(AdminMenuStates.block_user)
async def process_block_user_message_handler(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    is_admin: bool = False,
):
    if not await _check_admin(message, is_admin):
        return

    user_service = UserService(session=session, admin_id=settings.ADMIN_ID)
    raw_value = message.text or ""
    telegram_id, username = _split_identifier(raw_value)

    if telegram_id is None and username is None:
        return await message.answer(
            "⚠️ Укажите ID или username пользователя.\nПример: 123456 или @username.",
            reply_markup=admin_back_to_main_keyboard(),
        )

    if telegram_id is not None:
        user = await user_service.deactivate_user(telegram_id=telegram_id)
        target_label = str(telegram_id)
    else:
        user = await user_service.deactivate_user_by_username(username=username or "")
        target_label = f"@{username}"

    if user is None:
        text = "Пользователь не найден. Проверьте данные."
    else:
        text = f"⛔ Пользователь {target_label} заблокирован."

    await state.set_state(AdminMenuStates.block_user)
    return await message.answer(
        f"{text}\n\nВведите следующий ID или вернитесь в главное меню.",
        reply_markup=admin_back_to_main_keyboard(),
    )
