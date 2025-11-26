from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import NKOData
from src.schemas.nko import NKODataCreateSchema, NKODataUpdateSchema


class NKORepository:
    """CRUD-операции над данными НКО."""

    async def get_by_user_id(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> Optional[NKOData]:
        """Получить данные НКО по user_id."""
        query = select(NKOData).where(NKOData.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        user_id: int,
        data: NKODataCreateSchema,
    ) -> NKOData:
        """Создать запись НКО из схемы."""
        fields = data.to_model_fields()
        nko = NKOData(
            user_id=user_id,
            **fields,
        )
        session.add(nko)
        await session.flush()
        return nko

    async def update(
        self,
        session: AsyncSession,
        user_id: int,
        data: NKODataUpdateSchema,
    ) -> Optional[NKOData]:
        """Обновить запись НКО из схемы."""
        nko = await self.get_by_user_id(session=session, user_id=user_id)
        if nko is None:
            return None

        fields = data.to_model_fields()
        for key, value in fields.items():
            setattr(nko, key, value)

        await session.flush()
        return nko

    async def delete_by_user_id(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> bool:
        """Удалить запись НКО по user_id."""
        query = delete(NKOData).where(NKOData.user_id == user_id)
        result = await session.execute(query)
        await session.flush()
        return result.rowcount == 1
