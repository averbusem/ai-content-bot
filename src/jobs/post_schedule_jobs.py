from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from aiogram import Bot

from src.bot import bot as telegram_bot
from src.db.database import session_factory
from src.db.models import Post
from src.repositories.posts import PostRepository


logger = logging.getLogger(__name__)


post_repository = PostRepository()


def _get_bot() -> Bot:
    """
    Возвращает экземпляр бота.

    Вынесено в функцию, чтобы при необходимости было проще заменить реализацию.
    """
    return telegram_bot


def _build_post_preview_text(post: Post) -> str:
    """
    Формирует краткое текстовое резюме поста для напоминания.
    """
    content = post.content or {}
    text: Optional[str] = content.get("text")

    if text:
        # Обрезаем слишком длинный текст, чтобы напоминание оставалось компактным
        max_len = 500
        preview = text if len(text) <= max_len else text[: max_len - 3] + "..."
    else:
        preview = "Запланирован пост без текстового описания."

    return f"Напоминание о запланированном посте:\n\n{preview}\n\nВыберите действие:"


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

            text = _build_post_preview_text(post)

            await bot.send_message(
                chat_id=post.user_id,
                text=text,
            )

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
