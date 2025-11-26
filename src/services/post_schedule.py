from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from apscheduler.jobstores.base import JobLookupError
from sqlalchemy.ext.asyncio import AsyncSession

from src.jobs.post_schedule_jobs import send_reminder_job
from src.jobs.scheduler import get_scheduler
from src.repositories.posts import PostRepository
from src.schemas.posts import (
    PostContentSchema,
    PostCreateSchema,
    PostCreateDataSchema,
    PostScheduleCreateSchema,
    PostScheduleInputSchema,
    ScheduledPostReadSchema,
)

logger = logging.getLogger(__name__)


MOSCOW_TIME_FORMAT = "%d.%m.%Y %H:%M"
TIME_VALIDATION_BUFFER_MINUTES = 1


def _parse_moscow_time_to_utc(publish_at_local: str) -> datetime:
    """
    Парсит локальное время по Мск и возвращает datetime в UTC.

    Ожидаемый формат: 'DD.MM.YYYY HH:MM'.
    """
    try:
        naive_dt = datetime.strptime(publish_at_local, MOSCOW_TIME_FORMAT)
    except ValueError as e:  # pragma: no cover - защитный блок
        msg = f"Некорректный формат времени: {publish_at_local!r}. Ожидается DD.MM.YYYY HH:MM"
        raise ValueError(msg) from e

    # Вся логика в приложении крутится вокруг UTC, поэтому просто считаем,
    # что вход — это локальное московское время, смещённое относительно UTC.
    # Здесь нет прямой зависимости от tz-библиотек, что упрощает развёртывание.
    # Мск = UTC+3 (фиксируем, так как переходов на летнее время нет).
    moscow_offset = timedelta(hours=3)
    moscow_dt = naive_dt.replace(tzinfo=timezone(moscow_offset))
    return moscow_dt.astimezone(timezone.utc)


def _normalize_schedule_input(
    schedule_input: PostScheduleInputSchema,
) -> PostScheduleCreateSchema:
    """
    Преобразует входные данные пользователя в нормализованное расписание (UTC).
    """
    publish_at_utc = _parse_moscow_time_to_utc(schedule_input.publish_at)

    # Валидация: не даём запланировать пост "в прошлое"
    now_utc = datetime.now(timezone.utc)
    buffer = timedelta(minutes=TIME_VALIDATION_BUFFER_MINUTES)
    if publish_at_utc < now_utc + buffer:
        raise ValueError("Время публикации уже прошло или слишком близко к текущему.")

    remind_offset = timedelta(minutes=schedule_input.remind_offset_minutes)
    remind_at = publish_at_utc - remind_offset

    return PostScheduleCreateSchema(
        publish_at=publish_at_utc,
        remind_at=remind_at,
        remind_offset=remind_offset,
        state="pending",
    )


class PostScheduleService:
    """Бизнес-логика для планирования и управления запланированными постами."""

    def __init__(
        self,
        session: AsyncSession,
        repository: Optional[PostRepository] = None,
    ):
        self.session = session
        self.repository = repository or PostRepository()

    async def schedule_post(
        self,
        *,
        user_id: int,
        chat_id: int,
        content: PostContentSchema,
        schedule_input: PostScheduleInputSchema,
    ) -> ScheduledPostReadSchema:
        """
        Создаёт запланированный пост, регистрирует job'ы в APScheduler и возвращает DTO.
        """
        schedule_data = _normalize_schedule_input(schedule_input)

        post_create = PostCreateSchema(
            user_id=user_id,
            chat_id=chat_id,
            content=content,
        )

        data = PostCreateDataSchema(
            user_id=post_create.user_id,
            chat_id=post_create.chat_id,
            content=post_create.content,
            status="scheduled",
            publish_at=schedule_data.publish_at,
            remind_offset=schedule_data.remind_offset,
            remind_at=schedule_data.remind_at,
            state=schedule_data.state,
        )

        post = await self.repository.create_post(session=self.session, data=data)

        scheduler = get_scheduler()

        remind_job = scheduler.add_job(
            send_reminder_job,
            trigger="date",
            run_date=schedule_data.remind_at,
            args=[UUID(post.id)],
        )

        post.aps_job_id_remind = remind_job.id

        await self.session.commit()

        logger.info(
            "Scheduled post created: post_id=%s, remind_job_id=%s",
            post.id,
            post.aps_job_id_remind,
        )

        return ScheduledPostReadSchema.from_model(post)

    async def postpone(
        self,
        post_id: UUID,
        new_publish_at_local: str,
        new_remind_offset_minutes: int,
    ) -> ScheduledPostReadSchema:
        """
        Для будущего функционала.
        Переносит время публикации и напоминания, перепланируя job'ы APScheduler.
        """
        post = await self.repository.get_by_id(session=self.session, post_id=post_id)
        if post is None:
            raise ValueError(f"Post not found. post_id={post_id}")

        schedule_input = PostScheduleInputSchema(
            publish_at=new_publish_at_local,
            remind_offset_minutes=new_remind_offset_minutes,
        )
        schedule_data = _normalize_schedule_input(schedule_input)

        scheduler = get_scheduler()
        if post.aps_job_id_remind:
            try:
                scheduler.remove_job(post.aps_job_id_remind)
            except JobLookupError:
                logger.info(
                    "Job already removed or not found in postpone. post_id=%s, job_id=%s",
                    post_id,
                    post.aps_job_id_remind,
                )

        post.publish_at = schedule_data.publish_at
        post.remind_at = schedule_data.remind_at
        post.remind_offset = schedule_data.remind_offset

        remind_job = scheduler.add_job(
            send_reminder_job,
            trigger="date",
            run_date=schedule_data.remind_at,
            args=[post_id],
        )
        post.aps_job_id_remind = remind_job.id

        await self.session.commit()

        logger.info(
            "Post postponed: post_id=%s, new_publish_at=%s, new_remind_at=%s",
            post_id,
            post.publish_at,
            post.remind_at,
        )

        return ScheduledPostReadSchema.from_model(post)

    async def cancel(
        self,
        post_id: UUID,
    ) -> None:
        """
        Для будущего функционала.
        Отменяет запланированный пост и удаляет связанные job'ы APScheduler.
        """
        post = await self.repository.get_by_id(session=self.session, post_id=post_id)
        if post is None:
            logger.warning("Post not found in cancel. post_id=%s", post_id)
            return

        post.status = "cancelled"
        post.state = "cancelled"

        scheduler = get_scheduler()
        if post.aps_job_id_remind:
            try:
                scheduler.remove_job(post.aps_job_id_remind)
            except JobLookupError:
                logger.info(
                    "Job already removed or not found in cancel. post_id=%s, job_id=%s",
                    post_id,
                    post.aps_job_id_remind,
                )

        post.aps_job_id_remind = None

        await self.session.commit()

        logger.info("Post cancelled: post_id=%s", post_id)

    async def update_content(
        self,
        post_id: UUID,
        new_content: PostContentSchema,
    ) -> None:
        """
        Для будущего функционала.
        Обновляет контент поста в БД.
        """
        updated = await self.repository.update_content(
            session=self.session,
            post_id=post_id,
            content=new_content.model_dump(),
        )
        if updated is None:
            logger.warning("Post not found in update_content. post_id=%s", post_id)
            return

        await self.session.commit()
