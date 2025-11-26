from __future__ import annotations

from typing import Optional

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncEngine


_scheduler: Optional[AsyncIOScheduler] = None


def init_scheduler(engine: AsyncEngine) -> AsyncIOScheduler:
    """
    Инициализирует глобальный AsyncIOScheduler с SQLAlchemyJobStore.

    В качестве подключения к БД используется тот же engine, что и у приложения.
    """
    global _scheduler

    if _scheduler is not None:
        return _scheduler

    job_stores = {
        "default": SQLAlchemyJobStore(engine=engine),
    }

    scheduler = AsyncIOScheduler(jobstores=job_stores, timezone="UTC")
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
