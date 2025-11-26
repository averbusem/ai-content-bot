from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .models.gigachat import GigaChatModel
from .models.salute import SaluteSpeechModel
from .content_generator import ContentGenerator
from .image_generator import ImageGenerator
from .nko import NKOService
from .text_overlay import TextOverlayConfig, TextOverlayService


class AIManager:
    def __init__(self):
        self.gigachat = GigaChatModel()
        self.salute_speech = SaluteSpeechModel()
        self.content_generator = ContentGenerator(self.gigachat)
        text_overlay_service = TextOverlayService()
        self.image_generator = ImageGenerator(
            self.gigachat, text_overlay_service=text_overlay_service
        )

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ТЕКСТОМ ===

    async def _apply_ngo_context(self, session: AsyncSession, user_id: int) -> None:
        nko_service = NKOService(session=session)
        ngo_info = await nko_service.get_data(user_id)
        if ngo_info:
            self.content_generator.set_ngo_info(ngo_info)
        else:
            self.content_generator.ngo_info = None

    async def generate_free_text_post(
        self,
        user_id: int,
        session: AsyncSession,
        user_idea: str,
        style: str = "разговорный",
        additional_info: Optional[str] = None,
    ) -> str:
        """Генерация свободного текста поста"""
        await self._apply_ngo_context(session=session, user_id=user_id)

        return await self.content_generator.generate_free_text_post(
            user_idea=user_idea, style=style, additional_info=additional_info
        )

    async def generate_structured_post(
        self,
        user_id: int,
        session: AsyncSession,
        event_type: str,
        date: str,
        location: str,
        participants: str,
        details: str,
        style: str = "разговорный",
    ) -> str:
        """Генерация структурированного поста"""
        await self._apply_ngo_context(session=session, user_id=user_id)

        return await self.content_generator.generate_structured_post(
            event_type=event_type,
            date=date,
            location=location,
            participants=participants,
            details=details,
            style=style,
        )

    async def generate_structured_form_post(
        self,
        user_id: int,
        session: AsyncSession,
        event: str,
        description: str,
        goal: str,
        date: Optional[str] = None,
        location: Optional[str] = None,
        platform: str = "universal",
        audience: str = "broad",
        style: str = "warm",
        length: str = "medium",
        additional_info: Optional[str] = None,
    ) -> str:
        """Генерация поста на основе структурированной формы (10 вопросов)"""
        await self._apply_ngo_context(session=session, user_id=user_id)

        return await self.content_generator.generate_structured_form_post(
            event=event,
            description=description,
            goal=goal,
            date=date,
            location=location,
            platform=platform,
            audience=audience,
            style=style,
            length=length,
            additional_info=additional_info,
        )

    async def generate_post_from_example(
        self,
        user_id: int,
        session: AsyncSession,
        example_post: str,
        new_topic: str,
        style: Optional[str] = None,
    ) -> str:
        """Генерация поста на основе примера"""
        await self._apply_ngo_context(session=session, user_id=user_id)

        return await self.content_generator.generate_post_from_example(
            example_post=example_post, new_topic=new_topic, style=style
        )

    async def edit_post(
        self,
        user_id: int,
        session: AsyncSession,
        original_post: str,
        edit_request: str,
    ) -> tuple[str, list[str], list[str]]:
        """Редактирование поста на основе запроса пользователя"""
        await self._apply_ngo_context(session=session, user_id=user_id)
        return await self.content_generator.edit_post(
            original_post=original_post, edit_request=edit_request
        )

    async def generate_content_plan(
        self,
        user_id: int,
        session: AsyncSession,
        duration_days: int,
        posts_per_week: int,
        preferences: Optional[str] = None,
    ) -> str:
        """Создание контент-плана"""
        await self._apply_ngo_context(session=session, user_id=user_id)

        return await self.content_generator.generate_content_plan(
            duration_days=duration_days,
            posts_per_week=posts_per_week,
            preferences=preferences,
        )

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ ===

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        overlay_text: Optional[str] = None,
        overlay_font: Optional[str] = None,
        overlay_config: Optional[TextOverlayConfig] = None,
    ) -> bytes:
        """
        Генерация изображения

        Args:
            prompt: Промпт для генерации
            width: Ширина
            height: Высота

        Returns:
            Байты изображения
        """
        return await self.image_generator.generate_image(
            prompt=prompt,
            width=width,
            height=height,
            overlay_text=overlay_text,
            overlay_font=overlay_font,
            overlay_config=overlay_config,
        )

    async def generate_image_from_post(
        self,
        post_text: str,
        image_description: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        include_info_block: bool = False,
        prepared_info_text: Optional[str] = None,
        overlay_font: Optional[str] = None,
        overlay_config: Optional[TextOverlayConfig] = None,
    ) -> bytes:
        """Генерация изображения на основе текста поста"""
        return await self.image_generator.generate_image_from_post(
            post_text=post_text,
            image_description=image_description,
            width=width,
            height=height,
            include_info_block=include_info_block,
            prepared_info_text=prepared_info_text,
            overlay_font=overlay_font,
            overlay_config=overlay_config,
        )

    async def edit_image(
        self,
        source_image_data: bytes,
        edit_request: str,
        width: int = 1024,
        height: int = 1024,
    ) -> bytes:
        """
        Редактирование существующего изображения

        Args:
            source_image_data: Байты исходного изображения
            edit_request: Описание требуемых изменений
            width: Ширина результата
            height: Высота результата

        Returns:
            Байты отредактированного изображения
        """
        return await self.image_generator.edit_image(
            source_image_data=source_image_data,
            edit_request=edit_request,
            width=width,
            height=height,
        )

    async def create_image_from_example(
        self,
        example_image_data: bytes,
        creation_request: str,
        width: int = 1024,
        height: int = 1024,
    ) -> bytes:
        """
        Создание нового изображения на основе примера

        Args:
            example_image_data: Байты изображения-примера
            creation_request: Описание того, что нужно создать
            width: Ширина результата
            height: Высота результата

        Returns:
            Байты нового изображения
        """
        return await self.image_generator.create_from_example(
            example_image_data=example_image_data,
            creation_request=creation_request,
            width=width,
            height=height,
        )

    # === МЕТОДЫ ДЛЯ РАБОТЫ С АУДИО ===

    async def transcribe_voice(
        self, audio_data: bytes, audio_format: str = "opus"
    ) -> str:
        return await self.salute_speech.transcribe_audio(
            audio_data=audio_data, audio_format=audio_format
        )

    async def transcribe_voice_file(self, file_path: str) -> str:
        return await self.salute_speech.transcribe_from_file(file_path)

    def clear_conversation_history(self):
        self.gigachat.clear_history()

    def get_conversation_history(self):
        return self.gigachat.get_history()


ai_manager = AIManager()
