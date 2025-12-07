from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ContentPlan, ContentPlanDay
from src.repositories.content_plan import (
    ContentPlanRepository,
    ContentPlanDayRepository,
)
from src.services.content_plan_parser import ContentPlanParser


class ContentPlanService:
    """Сервис для работы с контент-планами."""

    def __init__(
        self,
        session: AsyncSession,
        plan_repository: Optional[ContentPlanRepository] = None,
        day_repository: Optional[ContentPlanDayRepository] = None,
    ):
        self.session = session
        self.plan_repository = plan_repository or ContentPlanRepository()
        self.day_repository = day_repository or ContentPlanDayRepository()
        self.parser = ContentPlanParser()

    async def save_content_plan(
        self,
        user_id: int,
        content: str,
        duration_days: int,
        posts_per_week: int,
        preferences: Optional[str] = None,
        name: Optional[str] = None,
    ) -> ContentPlan:
        """Сохранить контент-план в БД."""
        if name is None:
            name = self.parser.generate_plan_name(duration_days, posts_per_week)

        plan = await self.plan_repository.create(
            session=self.session,
            user_id=user_id,
            name=name,
            content=content,
            duration_days=duration_days,
            posts_per_week=posts_per_week,
            preferences=preferences,
        )

        days_data = self.parser.parse_content_plan(content)
        for day_data in days_data:
            await self.day_repository.create(
                session=self.session,
                content_plan_id=plan.id,
                day_name=day_data["day_name"],
                date=day_data["date"],
                time=day_data["time"],
                post_type=day_data["post_type"],
                topic=day_data["topic"],
                format=day_data["format"],
                week=day_data["week"],
            )

        await self.session.commit()
        return plan

    async def get_user_plans(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 5,
    ) -> tuple[List[ContentPlan], int]:
        """Получить контент-планы пользователя с пагинацией."""
        offset = (page - 1) * per_page
        plans = await self.plan_repository.get_by_user_id(
            session=self.session,
            user_id=user_id,
            limit=per_page,
            offset=offset,
        )
        total = await self.plan_repository.count_by_user_id(
            session=self.session,
            user_id=user_id,
        )
        return plans, total

    async def get_plan_by_id(
        self,
        plan_id: int,
    ) -> Optional[ContentPlan]:
        """Получить контент-план по ID."""
        return await self.plan_repository.get_by_id(
            session=self.session,
            plan_id=plan_id,
        )

    async def get_plan_days(
        self,
        plan_id: int,
        page: int = 1,
        per_page: int = 5,
    ) -> tuple[List[ContentPlanDay], int]:
        """Получить дни контент-плана с пагинацией."""
        offset = (page - 1) * per_page
        days = await self.day_repository.get_by_plan_id(
            session=self.session,
            plan_id=plan_id,
            limit=per_page,
            offset=offset,
        )
        total = await self.day_repository.count_by_plan_id(
            session=self.session,
            plan_id=plan_id,
        )
        return days, total

    async def get_day_by_id(
        self,
        day_id: int,
    ) -> Optional[ContentPlanDay]:
        """Получить день контент-плана по ID."""
        return await self.day_repository.get_by_id(
            session=self.session,
            day_id=day_id,
        )

    async def delete_content_plan(self, user_id: int, plan_id: int) -> bool:
        """
        Удалить контент-план пользователя.

        Удаляются сам план и все связанные дни
        """
        plan = await self.plan_repository.get_by_id(
            session=self.session,
            plan_id=plan_id,
        )
        if plan is None or plan.user_id != user_id:
            return False

        await self.session.delete(plan)
        await self.session.commit()
        return True
