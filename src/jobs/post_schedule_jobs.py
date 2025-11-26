from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Optional
from uuid import UUID

from aiogram import Bot
from src.db.database import session_factory
from src.db.models import Post
from src.repositories.posts import PostRepository


logger = logging.getLogger(__name__)


post_repository = PostRepository()


def _format_datetime_moscow(dt_utc: datetime) -> str:
    """
    Преобразует UTC datetime в строку по Мск в человекочитаемом формате.
    """
    moscow_dt = dt_utc.astimezone(timezone(timedelta(hours=3)))
    return moscow_dt.strftime("%d.%m.%Y %H:%M")


def _get_bot() -> Bot:
    """
    Возвращает экземпляр бота.

    Вынесено в функцию, чтобы при необходимости было проще заменить реализацию.
    """
    # Ленивая загрузка, чтобы избежать циклического импорта при инициализации бота.
    from src.bot import bot as telegram_bot  # noqa: WPS433

    return telegram_bot


def _build_post_preview_text(post: Post) -> str:
    """
    Формирует текстовое содержимое поста для напоминания без обрезки.
    """
    content = post.content or {}
    text: Optional[str] = content.get("text")

    if text:
        return text

    return "Запланирован пост без текстового описания."


async def send_reminder_job(post_id: UUID) -> None:
    """
    Джоба APScheduler: отправка напоминания пользователю о запланированном посте.
    """
    async with session_factory() as session:  # type: AsyncSession
        try:
            post = await post_repository.get_by_id(session=session, post_id=post_id)
            if post is None:
                logger.warning("Post not found for reminder job. post_id=%s", post_id)
                return

            # Проверяем актуальность поста
            if post.state != "pending" or post.status in ("published", "cancelled"):
                logger.info(
                    "Skip reminder job for post_id=%s due to state/status: state=%s, status=%s",
                    post_id,
                    post.state,
                    post.status,
                )
                return

            bot = _get_bot()

            # Сначала отправляем служебное сообщение-напоминание с указанием времени публикации
            moscow_publish_at = _format_datetime_moscow(post.publish_at)
            await bot.send_message(
                chat_id=post.user_id,
                text=f"Напоминание о запланированном посте {moscow_publish_at}",
            )

            # Затем отправляем сам пост целиком (как при публикации),
            # но в личку пользователю
            content = post.content or {}
            text: Optional[str] = content.get("text")
            photo_file_id: Optional[str] = content.get("photo_file_id")

            if photo_file_id is not None:
                # Есть картинка — отправляем её с подписью (если есть)
                if text:
                    await bot.send_photo(
                        chat_id=post.user_id,
                        photo=photo_file_id,
                        caption=text,
                    )
                else:
                    await bot.send_photo(
                        chat_id=post.user_id,
                        photo=photo_file_id,
                    )
            else:
                # Только текстовый пост
                if text:
                    await bot.send_message(chat_id=post.user_id, text=text)
                else:
                    logger.info(
                        "Post content is empty for post_id=%s, nothing to send in reminder",
                        post_id,
                    )
                    return

            # Обновляем состояние поста
            post.state = "reminded"
            await session.commit()

            logger.info("Reminder sent successfully for post_id=%s", post_id)

        except Exception:
            logger.exception(
                "Error while executing send_reminder_job for post_id=%s", post_id
            )
            # Важно не поднимать исключение выше, чтобы APScheduler не падал


async def publish_scheduled_post_job(post_id: UUID) -> None:
    """
    Джоба APScheduler: автопубликация запланированного поста.
    """
    async with session_factory() as session:  # type: AsyncSession
        try:
            post = await post_repository.get_by_id(session=session, post_id=post_id)
            if post is None:
                logger.warning("Post not found for publish job. post_id=%s", post_id)
                return

            # Публикуем только запланированные посты в допустимом состоянии
            if post.status != "scheduled" or post.state in ("published", "cancelled"):
                logger.info(
                    "Skip publish job for post_id=%s due to state/status: state=%s, status=%s",
                    post_id,
                    post.state,
                    post.status,
                )
                return

            bot = _get_bot()

            content = post.content or {}
            text: Optional[str] = content.get("text")
            photo_file_id: Optional[str] = content.get("photo_file_id")

            # Если есть картинка — отправляем её (с подписью или без)
            if photo_file_id is not None:
                if text:
                    await bot.send_photo(
                        chat_id=post.chat_id,
                        photo=photo_file_id,
                        caption=text,
                    )
                else:
                    await bot.send_photo(
                        chat_id=post.chat_id,
                        photo=photo_file_id,
                    )
            else:
                # Только текстовый пост
                if text:
                    await bot.send_message(chat_id=post.chat_id, text=text)
                else:
                    logger.info(
                        "Post content is empty for post_id=%s, nothing to publish",
                        post_id,
                    )
                    return

            # Обновляем статусы и очищаем ID job'ов
            post.status = "published"
            post.state = "published"
            post.aps_job_id_remind = None
            post.aps_job_id_publish = None

            await session.commit()

            logger.info("Post published successfully for post_id=%s", post_id)

        except Exception:
            logger.exception(
                "Error while executing publish_scheduled_post_job for post_id=%s",
                post_id,
            )
            # Не пробрасываем исключение выше
