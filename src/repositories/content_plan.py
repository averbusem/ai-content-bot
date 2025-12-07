from typing import Optional, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ContentPlan, ContentPlanDay


class ContentPlanRepository:
    """CRUD-операции над контент-планами."""

    async def create(
        self,
        session: AsyncSession,
        user_id: int,
        name: str,
        content: str,
        duration_days: int,
        posts_per_week: int,
        preferences: Optional[str] = None,
    ) -> ContentPlan:
        """Создать контент-план."""
        plan = ContentPlan(
            user_id=user_id,
            name=name,
            content=content,
            duration_days=duration_days,
            posts_per_week=posts_per_week,
            preferences=preferences,
        )
        session.add(plan)
        await session.flush()
        return plan

    async def get_by_id(
        self,
        session: AsyncSession,
        plan_id: int,
    ) -> Optional[ContentPlan]:
        """Получить контент-план по ID."""
        query = select(ContentPlan).where(ContentPlan.id == plan_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 5,
        offset: int = 0,
    ) -> List[ContentPlan]:
        """Получить контент-планы пользователя с пагинацией."""
        query = (
            select(ContentPlan)
            .where(ContentPlan.user_id == user_id)
            .order_by(desc(ContentPlan.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_by_user_id(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int:
        """Подсчитать количество контент-планов пользователя."""
        query = select(func.count(ContentPlan.id)).where(ContentPlan.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one() or 0

    async def delete(
        self,
        session: AsyncSession,
        plan_id: int,
    ) -> bool:
        """Удалить контент-план по ID."""
        plan = await self.get_by_id(session=session, plan_id=plan_id)
        if plan is None:
            return False
        await session.delete(plan)
        await session.flush()
        return True


class ContentPlanDayRepository:
    """CRUD-операции над днями контент-плана."""

    async def create(
        self,
        session: AsyncSession,
        content_plan_id: int,
        day_name: str,
        date: str,
        time: str,
        post_type: Optional[str],
        topic: Optional[str],
        format: Optional[str],
        week: int,
    ) -> ContentPlanDay:
        """Создать день контент-плана."""
        day = ContentPlanDay(
            content_plan_id=content_plan_id,
            day_name=day_name,
            date=date,
            time=time,
            post_type=post_type,
            topic=topic,
            format=format,
            week=week,
        )
        session.add(day)
        await session.flush()
        return day

    async def get_by_plan_id(
        self,
        session: AsyncSession,
        plan_id: int,
        limit: int = 5,
        offset: int = 0,
    ) -> List[ContentPlanDay]:
        """Получить дни контент-плана с пагинацией."""
        query = (
            select(ContentPlanDay)
            .where(ContentPlanDay.content_plan_id == plan_id)
            .order_by(ContentPlanDay.week, ContentPlanDay.date, ContentPlanDay.time)
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_by_plan_id(
        self,
        session: AsyncSession,
        plan_id: int,
    ) -> int:
        """Подсчитать количество дней в контент-плане."""
        query = select(func.count(ContentPlanDay.id)).where(
            ContentPlanDay.content_plan_id == plan_id
        )
        result = await session.execute(query)
        return result.scalar_one() or 0

    async def get_by_id(
        self,
        session: AsyncSession,
        day_id: int,
    ) -> Optional[ContentPlanDay]:
        """Получить день контент-плана по ID."""
        query = select(ContentPlanDay).where(ContentPlanDay.id == day_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
