import logging
from typing import Optional, Tuple

from aiogram import BaseMiddleware, Bot, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import back_to_menu_keyboard
from src.db.database import session_factory
from src.db.models import User
from src.services.user import UserService

logger = logging.getLogger(__name__)


class DBSessionMiddleware(BaseMiddleware):
    """
    Открывает AsyncSession перед обработкой и роллбекает при ошибке.
    """

    async def __call__(self, handler, event: TelegramObject, data: dict):
        async with session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                return result
            except Exception as e:
                await session.rollback()
                logger.exception(
                    "Error in middleware %s for event %s Exception %s",
                    handler.__name__,
                    event,
                    e,
                )
                return await _send_error_message(event)


async def _send_error_message(event: TelegramObject):
    """Отправка сообщения об ошибке пользователю"""
    text = "⚠️ Произошла ошибка при обработке запроса. Напишите в поддержку."
    if isinstance(event, CallbackQuery) and event.message:
        return await event.message.answer(
            text,
            reply_markup=back_to_menu_keyboard(),
        )
    if isinstance(event, Message):
        return await event.answer(
            text,
            reply_markup=back_to_menu_keyboard(),
        )
    return None


class UserAccessMiddleware(BaseMiddleware):
    """
    Проверяет доступ пользователя к боту.

    Пропускает администратора и активных пользователей. Остальным отвечает,
    что доступ ещё не открыт, и при первой заявке уведомляет администратора.
    """

    def __init__(self, bot: Bot, admin_id: int):
        self.bot = bot
        self.admin_id = admin_id

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict,
    ):
        session: Optional[AsyncSession] = data.get("session")
        from_user = self._extract_user(event)

        if session is None or from_user is None:
            return await handler(event, data)

        telegram_id = from_user.id
        username = from_user.username

        user_service = UserService(
            session=session,
            bot=self.bot,
            admin_id=self.admin_id,
        )

        if telegram_id == self.admin_id:
            await user_service.ensure_admin_user(
                telegram_id=telegram_id,
                username=username,
            )
            data["is_admin"] = True
            return await handler(event, data)

        user, created = await self._ensure_user(
            user_service=user_service,
            telegram_id=telegram_id,
            username=username,
        )

        if user and user.is_active:
            data["current_user"] = user
            data["is_admin"] = False
            return await handler(event, data)

        if created:
            await self._notify_admin(user_service=user_service, user=user)
            return await self._respond(
                event,
                "🚧 Заявка отправлена администратору. Ожидайте подтверждения.",
            )

        return await self._respond(
            event,
            "⏳ Ваша заявка уже на рассмотрении. Пожалуйста, ожидайте доступа.",
        )

    async def _ensure_user(
        self,
        user_service: UserService,
        telegram_id: int,
        username: Optional[str],
    ) -> Tuple[User, bool]:
        try:
            return await user_service.register_or_get_user(
                telegram_id=telegram_id,
                username=username,
            )
        except Exception:
            logger.exception("Не удалось зарегистрировать пользователя %s", telegram_id)
            raise

    async def _notify_admin(self, user_service: UserService, user) -> None:
        if user is None:
            return
        try:
            await user_service.send_access_request_to_admin(
                user=user,
                text=(
                    f"Пользователь {user.username or 'без username'} "
                    f"({user.telegram_id}) запрашивает доступ.\n\n"
                    "Откройте /admin → «Посмотреть запросы», чтобы выдать доступ."
                ),
            )
        except Exception:
            logger.exception(
                "Не удалось отправить запрос на доступ админу от %s", user.telegram_id
            )

    async def _respond(self, event: TelegramObject, text: str):
        if isinstance(event, CallbackQuery):
            try:
                await event.answer()
            except TelegramBadRequest:
                pass
            if event.message:
                return await event.message.answer(text)
            return await self.bot.send_message(chat_id=event.from_user.id, text=text)
        if isinstance(event, Message):
            return await event.answer(text)
        return None

    @staticmethod
    def _extract_user(event: TelegramObject) -> Optional[types.User]:
        if isinstance(event, Message):
            return event.from_user
        if isinstance(event, CallbackQuery):
            return event.from_user
        return None


class RemoveLastKeyboardMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        state: FSMContext = data.get("state")
        data_state = await state.get_data()
        last_message_id = data_state.get("last_message_id")

        result = await handler(event, data)

        current_message_id = None
        if isinstance(result, types.Message):
            current_message_id = result.message_id
        elif isinstance(event, types.CallbackQuery):
            current_message_id = event.message.message_id

        if (
            last_message_id
            and current_message_id
            and last_message_id != current_message_id
        ):
            chat_id = (
                event.message.chat.id
                if isinstance(event, types.CallbackQuery)
                else event.chat.id
            )
            await _remove_keyboard(event.bot, chat_id, last_message_id)

        if state and current_message_id:
            logger.debug(f"Update last_message_id = {current_message_id}")
            await state.update_data(last_message_id=current_message_id)
        return result


async def _remove_keyboard(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=message_id, reply_markup=None
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug(f"Keyboard already removed: {chat_id}:{message_id}")
            return
        logger.error(f"Error removing keyboard {chat_id}:{message_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error removing keyboard {chat_id}:{message_id}: {e}")
