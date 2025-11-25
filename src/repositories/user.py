from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


class UserRepository:
    """CRUD-операции над пользователями."""

    async def get_by_telegram_id(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> Optional[User]:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_pending_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str],
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            is_active=False,
        )
        session.add(user)
        await session.flush()
        return user

    async def activate_user(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> Optional[User]:
        user = await self.get_by_telegram_id(session=session, telegram_id=telegram_id)
        if user is None:
            return None

        user.is_active = True
        await session.flush()
        return user

    async def list_pending_users(
        self,
        session: AsyncSession,
    ) -> Sequence[User]:
        query = (
            select(User)
            .where(User.is_active.is_(False))
            .order_by(User.created_at.asc())
        )
        result = await session.execute(query)
        return result.scalars().all()
