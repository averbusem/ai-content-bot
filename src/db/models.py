from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    func,
)
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

    def __repr__(self):
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


# class ContentPlan(Base):
#     __tablename__ = "content_plans"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     user_id: Mapped[int] = mapped_column(
#         ForeignKey("users.telegram_id", ondelete="CASCADE"),
#         index=True,
#     )
#     scheduled_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True),
#         index=True,
#         doc="Дата и время публикации поста",
#     )
#     topic: Mapped[str] = mapped_column(Text, doc="Тема поста")
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True), server_default=func.now()
#     )
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
#     )
