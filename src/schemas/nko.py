from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field
from src.db.models import NKOData


class NKODataCreateSchema(BaseModel):
    """Схема для создания записи НКО из данных FSM state."""

    name: str = Field(..., min_length=1, max_length=255)
    activity: str = Field(..., min_length=1)
    forms: List[str] = Field(..., min_items=1)
    region: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = None
    website: Optional[str] = Field(None, max_length=255)

    def to_model_fields(self) -> Dict[str, Any]:
        # возвращает только заданные (и не None) поля
        return self.model_dump(exclude_none=True)


class NKODataUpdateSchema(BaseModel):
    """Схема для обновления записи НКО (все поля Optional)."""

    name: Optional[str] = Field(None, max_length=255)
    activity: Optional[str] = None
    forms: Optional[List[str]] = None
    region: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = None
    website: Optional[str] = Field(None, max_length=255)

    def to_model_fields(self) -> Dict[str, Any]:
        # возвращаем только поля, которые были указаны в update
        return self.model_dump(exclude_unset=True, exclude_none=True)


class NKODataResponseSchema(BaseModel):
    """Схема для возврата данных НКО (совместима с ContentGenerator)."""

    name: Optional[str] = None
    activity: Optional[str] = None
    forms: List[str] = Field(default_factory=list)
    region: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = Field(None, max_length=255)

    @classmethod
    def from_model(cls, nko: NKOData) -> "NKODataResponseSchema":
        return cls.model_validate(nko, from_attributes=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)
