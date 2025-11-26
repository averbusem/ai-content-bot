from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from src.db.models import Post


class PostContent(BaseModel):
    """Контент поста: текст + опциональная картинка."""

    text: str = Field(..., description="Текст поста")
    photo_file_id: Optional[str] = Field(
        default=None,
        description="file_id картинки в Telegram (если есть)",
    )


class PostCreate(BaseModel):
    """Данные для создания поста из FSM."""

    user_id: int
    chat_id: int
    content: PostContent


class PostScheduleInput(BaseModel):
    """
    Входные данные от пользователя для настройки расписания.

    publish_at — локальное время (строкой), например 'DD.MM.YYYY HH:MM' по Мск.
    """

    publish_at: str
    remind_offset_minutes: int
    auto_publish: bool = True


class PostScheduleCreate(BaseModel):
    """
    Нормализованные данные расписания для записи в БД.

    Все времена — в UTC.
    """

    publish_at: datetime
    remind_at: datetime
    remind_offset: timedelta
    auto_publish: bool
    state: str = "pending"
    aps_job_id_remind: Optional[str] = None
    aps_job_id_publish: Optional[str] = None


class PostCreateData(BaseModel):
    """
    Объединённые данные для создания Post в БД.

    Используется репозиторием: контент + нормализованное расписание.
    """

    id: Optional[str] = None
    user_id: int
    chat_id: int
    content: PostContent

    status: str = "scheduled"
    publish_at: datetime
    remind_offset: timedelta
    remind_at: datetime
    auto_publish: bool = False
    state: str = "pending"
    aps_job_id_remind: Optional[str] = None
    aps_job_id_publish: Optional[str] = None

    def to_model_fields(self) -> Dict[str, Any]:
        """Подготовить словарь полей для модели SQLAlchemy Post."""
        return self.model_dump(exclude_none=True)


class PostRead(BaseModel):
    """DTO поста для использования в сервисах/хэндлерах."""

    id: str
    user_id: int
    chat_id: int
    content: PostContent
    status: str
    publish_at: datetime
    remind_at: datetime
    auto_publish: bool
    state: str

    @classmethod
    def from_model(cls, post: Post) -> "PostRead":
        return cls.model_validate(post, from_attributes=True)


class ScheduledPostRead(BaseModel):
    """
    Удобная схема для возврата из сервисов.

    Содержит как основные поля поста, так и ключевую информацию о расписании.
    """

    id: str
    user_id: int
    chat_id: int
    content: PostContent
    status: str

    publish_at: datetime
    remind_at: datetime
    remind_offset: timedelta

    auto_publish: bool
    state: str

    aps_job_id_remind: Optional[str] = None
    aps_job_id_publish: Optional[str] = None

    @property
    def remind_offset_minutes(self) -> int:
        """Интервал напоминания в минутах (для удобства отображения)."""
        return int(self.remind_offset.total_seconds() // 60)

    @classmethod
    def from_model(cls, post: Post) -> "ScheduledPostRead":
        return cls.model_validate(post, from_attributes=True)
