import logging
from typing import Optional, Dict, Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import NKOData
from src.repositories.nko import NKORepository
from src.schemas.nko import (
    NKODataCreateSchema,
    NKODataUpdateSchema,
    NKODataResponseSchema,
)

logger = logging.getLogger(__name__)


class NKOService:
    """Бизнес-логика для управления данными НКО."""

    def __init__(
        self,
        session: AsyncSession,
        repository: Optional[NKORepository] = None,
    ):
        self.session = session
        self.repository = repository or NKORepository()

    async def get_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить данные НКО по user_id.

        Возвращает словарь, совместимый с ContentGenerator, или None если данных нет.
        """
        try:
            nko = await self.repository.get_by_user_id(
                session=self.session,
                user_id=user_id,
            )
            if nko is None:
                return None

            response_schema = NKODataResponseSchema.from_model(nko)
            return response_schema.to_dict()
        except Exception as e:
            logger.error(f"Ошибка при получении данных НКО для user_id={user_id}: {e}")
            raise

    async def save_data(self, user_id: int, data: Dict[str, Any]) -> NKOData:
        """
        Сохранить данные НКО (создать или обновить).

        Валидирует данные через Pydantic схемы и создает/обновляет запись.
        """
        try:
            existing_nko = await self.repository.get_by_user_id(
                session=self.session,
                user_id=user_id,
            )

            if existing_nko is None:
                create_schema = NKODataCreateSchema(**data)
                nko = await self.repository.create(
                    session=self.session,
                    user_id=user_id,
                    data=create_schema,
                )
            else:
                update_schema = NKODataUpdateSchema(**data)
                nko = await self.repository.update(
                    session=self.session,
                    user_id=user_id,
                    data=update_schema,
                )
                if nko is None:
                    raise ValueError(
                        f"Не удалось обновить данные НКО для user_id={user_id}"
                    )

            await self.session.commit()
            return nko
        except ValidationError as e:
            await self.session.rollback()
            error_messages = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                error_messages.append(f"{field}: {message}")
            error_text = "; ".join(error_messages)
            logger.warning(
                f"Ошибка валидации данных НКО для user_id={user_id}: {error_text}"
            )
            raise ValueError(f"Ошибка валидации данных: {error_text}") from e
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при сохранении данных НКО для user_id={user_id}: {e}")
            raise

    async def delete_data(self, user_id: int) -> bool:
        """
        Удалить данные НКО по user_id.

        Возвращает True если данные удалены, False если не найдены.
        """
        try:
            deleted = await self.repository.delete_by_user_id(
                session=self.session,
                user_id=user_id,
            )
            await self.session.commit()
            return deleted
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка при удалении данных НКО для user_id={user_id}: {e}")
            raise
