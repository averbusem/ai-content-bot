from __future__ import annotations

from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncEngine


_scheduler: Optional[AsyncIOScheduler] = None


def init_scheduler(_: AsyncEngine) -> AsyncIOScheduler:
    """
    Инициализирует глобальный AsyncIOScheduler без persistent jobstore (in-memory).

    Это упрощает конфигурацию и исключает проблемы с asyncpg в SQLAlchemyJobStore.
    Запланированные задачи не переживают перезапуск приложения.
    """
    global _scheduler

    if _scheduler is not None:
        return _scheduler

    scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler = scheduler
    return scheduler


def get_scheduler() -> AsyncIOScheduler:
    """
    Возвращает уже инициализированный AsyncIOScheduler.

    Должен вызываться только после init_scheduler.
    """
    if _scheduler is None:
        raise RuntimeError("Scheduler is not initialized. Call init_scheduler() first.")

    return _scheduler
