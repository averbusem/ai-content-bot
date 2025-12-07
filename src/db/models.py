from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Interval,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.db.database import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True)

    # Админ может поставить False, тогда бот будет недоступен
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class NKOData(Base):
    __tablename__ = "nko_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    activity: Mapped[str] = mapped_column(Text)
    forms: Mapped[list[str]] = mapped_column(
        JSON
    )  # список любых строк, включая «другое»
    region: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Post(Base):
    """
    Запланированный или опубликованный пост с настройками напоминания.
    """

    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        doc="UUID поста в строковом виде",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
        doc="Telegram ID пользователя, создавшего пост",
    )
    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        doc="Чат, в который нужно опубликовать пост",
    )
    content: Mapped[dict] = mapped_column(
        JSON,
        doc=(
            "Структура вида "
            '{"text": str | None, '
            '"media": [{"type": "photo|video|...", "file_id": str, "caption": str | None}]}'
        ),
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="scheduled",
        doc='Статус поста: "scheduled" | "published" | "cancelled"',
    )

    # Времена в UTC для планирования публикации и напоминаний
    publish_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        doc="Момент публикации поста (UTC)",
    )
    remind_offset: Mapped[timedelta] = mapped_column(
        Interval,
        doc="Интервал до публикации, когда нужно отправить напоминание",
    )
    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        doc="Время отправки напоминания (UTC)",
    )

    state: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        doc=('Состояние напоминания: "pending" | "reminded" | "published"'),
    )

    aps_job_id_remind: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="ID APScheduler-задачи для напоминания",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ContentPlan(Base):
    """Контент-план пользователя"""

    __tablename__ = "content_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), doc="Название контент-плана")
    content: Mapped[str] = mapped_column(Text, doc="Полный текст контент-плана")
    duration_days: Mapped[int] = mapped_column(doc="Длительность плана в днях")
    posts_per_week: Mapped[int] = mapped_column(doc="Количество постов в неделю")
    preferences: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Предпочтения пользователя"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ContentPlanDay(Base):
    """Отдельный день из контент-плана"""

    __tablename__ = "content_plan_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_plan_id: Mapped[int] = mapped_column(
        ForeignKey("content_plans.id", ondelete="CASCADE"),
        index=True,
    )
    day_name: Mapped[str] = mapped_column(
        String(10), doc="Название дня недели (ПН, ВТ, и т.д.)"
    )
    date: Mapped[str] = mapped_column(String(10), doc="Дата в формате ДД.ММ")
    time: Mapped[str] = mapped_column(String(10), doc="Время в формате ЧЧ:ММ")
    post_type: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Тип поста с эмодзи"
    )
    topic: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Тема поста")
    format: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Формат поста"
    )
    week: Mapped[int] = mapped_column(doc="Номер недели")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
