from typing import Optional, Sequence
from uuid import UUID, uuid4

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Post
from src.schemas.posts import PostCreateDataSchema


class PostRepository:
    """CRUD-операции над запланированными/опубликованными постами."""

    async def create_post(
        self,
        session: AsyncSession,
        data: PostCreateDataSchema,
    ) -> Post:
        """
        Создать пост на основе объединённых данных контента и расписания.

        Репозиторий не делает commit/rollback — это обязанность сервисного слоя.
        """
        fields = data.to_model_fields()

        # Генерируем UUID, если не был проставлен раньше
        if "id" not in fields or fields["id"] is None:
            fields["id"] = str(uuid4())

        post = Post(**fields)
        session.add(post)
        await session.flush()
        return post

    async def get_by_id(
        self,
        session: AsyncSession,
        post_id: UUID,
    ) -> Optional[Post]:
        """Получить пост по его UUID."""
        query: Select[tuple[Post]] = select(Post).where(Post.id == str(post_id))
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def update_content(
        self,
        session: AsyncSession,
        post_id: UUID,
        content: dict,
    ) -> Optional[Post]:
        """Обновить JSON-контент поста."""
        post = await self.get_by_id(session=session, post_id=post_id)
        if post is None:
            return None

        post.content = content
        await session.flush()
        return post

    async def update_status(
        self,
        session: AsyncSession,
        post_id: UUID,
        status: str,
    ) -> Optional[Post]:
        """Обновить статус поста."""
        post = await self.get_by_id(session=session, post_id=post_id)
        if post is None:
            return None

        post.status = status
        await session.flush()
        return post

    async def list_user_posts(
        self,
        session: AsyncSession,
        user_id: int,
        status: Optional[str] = None,
    ) -> Sequence[Post]:
        """
        Получить список постов пользователя.

        При переданном status фильтрует по статусу.
        """
        query: Select[tuple[Post]] = select(Post).where(Post.user_id == user_id)
        if status is not None:
            query = query.where(Post.status == status)

        query = query.order_by(Post.publish_at.asc())

        result = await session.execute(query)
        return result.scalars().all()
