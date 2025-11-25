from __future__ import annotations

from typing import Optional, Sequence, Tuple

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.repositories.user import UserRepository


class UserService:
    """Бизнес-логика для управления пользователями."""

    def __init__(
        self,
        session: AsyncSession,
        bot: Optional[Bot] = None,
        admin_id: Optional[int] = None,
        repository: Optional[UserRepository] = None,
    ):
        self.session = session
        self.bot = bot
        self.admin_id = admin_id
        self.repository = repository or UserRepository()

    async def register_or_get_user(
        self,
        telegram_id: int,
        username: Optional[str],
    ) -> Tuple[User, bool]:
        """
        Возвращает пользователя; если его нет — создаёт как неактивного.

        Возвращает кортеж (user, created).
        """
        try:
            user = await self.repository.get_by_telegram_id(
                session=self.session,
                telegram_id=telegram_id,
            )
            created = False

            if user is None:
                user = await self.repository.create_pending_user(
                    session=self.session,
                    telegram_id=telegram_id,
                    username=username,
                )
                created = True
            elif username and user.username != username:
                user.username = username
                await self.session.flush()

            await self.session.commit()
            return user, created
        except Exception:
            await self.session.rollback()
            raise

    async def activate_user(self, telegram_id: int) -> Optional[User]:
        """Активирует пользователя и фиксирует изменения."""
        try:
            user = await self.repository.activate_user(
                session=self.session,
                telegram_id=telegram_id,
            )
            await self.session.commit()
            return user
        except Exception:
            await self.session.rollback()
            raise

    async def list_pending_users(self) -> Sequence[User]:
        """Возвращает пользователей, ожидающих активации."""
        return await self.repository.list_pending_users(session=self.session)

    async def send_access_request_to_admin(
        self,
        user: User,
        text: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Message:
        """
        Отправляет админу уведомление о запросе доступа.

        Параметры текста и клавиатуры позволяют переиспользовать метод позже.
        """
        if self.bot is None or self.admin_id is None:
            raise ValueError(
                "Bot и admin_id должны быть заданы для отправки уведомлений"
            )

        message_text = text or (
            f"Пользователь {user.username or 'без username'} ({user.telegram_id}) запрашивает доступ."
        )
        return await self.bot.send_message(
            chat_id=self.admin_id,
            text=message_text,
            reply_markup=reply_markup,
        )
