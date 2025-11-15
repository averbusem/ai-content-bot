from typing import Optional, Dict, Any
from .models.gigachat import GigaChatModel
from .models.salute import SaluteSpeechModel
from .content_generator import ContentGenerator
from .image_generator import ImageGenerator
from .nko_service import nko_service


class AIManager:
    def __init__(self):
        # Инициализация GigaChat
        self.gigachat = GigaChatModel()

        # Инициализация Salute Speech
        self.salute_speech = SaluteSpeechModel()

        # Инициализация генератора контента
        self.content_generator = ContentGenerator(self.gigachat)

        # Инициализация генератора изображений
        self.image_generator = ImageGenerator(self.gigachat)

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ТЕКСТОМ ===

    async def generate_free_text_post(
        self,
        user_id: int,
        user_idea: str,
        style: str = "разговорный",
        additional_info: Optional[str] = None
    ) -> str:
        """Генерация свободного текста поста"""
        # Получаем данные НКО из Redis
        ngo_info = await nko_service.get_nko_data(user_id)
        if ngo_info:
            self.content_generator.set_ngo_info(ngo_info)
        else:
            self.content_generator.ngo_info = None

        return await self.content_generator.generate_free_text_post(
            user_idea=user_idea,
            style=style,
            additional_info=additional_info
        )

    async def generate_structured_post(
        self,
        user_id: int,
        event_type: str,
        date: str,
        location: str,
        participants: str,
        details: str,
        style: str = "разговорный"
    ) -> str:
        """Генерация структурированного поста"""
        # Получаем данные НКО из Redis
        ngo_info = await nko_service.get_nko_data(user_id)
        if ngo_info:
            self.content_generator.set_ngo_info(ngo_info)
        else:
            self.content_generator.ngo_info = None

        return await self.content_generator.generate_structured_post(
            event_type=event_type,
            date=date,
            location=location,
            participants=participants,
            details=details,
            style=style
        )

    async def generate_structured_form_post(
        self,
        user_id: int,
        event: str,
        description: str,
        goal: str,
        date: Optional[str] = None,
        location: Optional[str] = None,
        platform: str = "universal",
        audience: str = "broad",
        style: str = "warm",
        length: str = "medium",
        additional_info: Optional[str] = None
    ) -> str:
        """Генерация поста на основе структурированной формы (10 вопросов)"""
        # Получаем данные НКО из Redis
        ngo_info = await nko_service.get_nko_data(user_id)
        if ngo_info:
            self.content_generator.set_ngo_info(ngo_info)
        else:
            self.content_generator.ngo_info = None

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
            additional_info=additional_info
        )

    async def generate_post_from_example(
        self,
        user_id: int,
        example_post: str,
        new_topic: str,
        style: Optional[str] = None
    ) -> str:
        """Генерация поста на основе примера"""
        # Получаем данные НКО из Redis
        ngo_info = await nko_service.get_nko_data(user_id)
        if ngo_info:
            self.content_generator.set_ngo_info(ngo_info)
        else:
            self.content_generator.ngo_info = None

        return await self.content_generator.generate_post_from_example(
            example_post=example_post,
            new_topic=new_topic,
            style=style
        )

    async def edit_post(
        self,
        user_id: int,
        original_post: str,
        edit_request: str
    ) -> str:
        """Редактирование поста на основе запроса пользователя"""
        # Получаем данные НКО из Redis
        ngo_info = await nko_service.get_nko_data(user_id)
        if ngo_info:
            self.content_generator.set_ngo_info(ngo_info)
        else:
            self.content_generator.ngo_info = None
        return await self.content_generator.edit_post(
            original_post=original_post,
            edit_request=edit_request
        )

    async def edit_text(
        self,
        text: str,
        edit_focus: str = "все аспекты"
    ) -> Dict[str, Any]:
        """Редактирование текста"""
        return await self.content_generator.edit_text(
            text=text,
            edit_focus=edit_focus
        )

    async def generate_content_plan(
        self,
        user_id: int,
        duration_days: int,
        posts_per_week: int,
        preferences: Optional[str] = None
    ) -> str:
        """Создание контент-плана"""
        # Получаем данные НКО из Redis
        ngo_info = await nko_service.get_nko_data(user_id)
        if ngo_info:
            self.content_generator.set_ngo_info(ngo_info)
        else:
            self.content_generator.ngo_info = None

        return await self.content_generator.generate_content_plan(
            duration_days=duration_days,
            posts_per_week=posts_per_week,
            preferences=preferences
        )

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ ===

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> bytes:
        return await self.image_generator.generate_image(
            prompt=prompt,
            width=width,
            height=height
        )

    async def generate_image_from_params(
        self,
        description: str,
        style: str,
        colors: str,
        width: int = 1024,
        height: int = 1024
    ) -> bytes:
        """Генерация изображения на основе параметров пользователя"""
        return await self.image_generator.generate_image_from_params(
            description=description,
            style=style,
            colors=colors,
            width=width,
            height=height
        )

    async def generate_image_from_post(
        self,
        post_text: str,
        image_description: Optional[str] = None,
        width: int = 1024,
        height: int = 1024
    ) -> bytes:
        """Генерация изображения на основе текста поста"""
        return await self.image_generator.generate_image_from_post(
            post_text=post_text,
            image_description=image_description,
            width=width,
            height=height
        )

    # === МЕТОДЫ ДЛЯ РАБОТЫ С АУДИО ===

    async def transcribe_voice(
        self,
        audio_data: bytes,
        audio_format: str = "opus"
    ) -> str:
        return await self.salute_speech.transcribe_audio(
            audio_data=audio_data,
            audio_format=audio_format
        )

    async def transcribe_voice_file(
        self,
        file_path: str
    ) -> str:
        return await self.salute_speech.transcribe_from_file(file_path)

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def clear_conversation_history(self):
        """Очистка истории диалога"""
        self.gigachat.clear_history()

    def get_conversation_history(self):
        """Получение истории диалога"""
        return self.gigachat.get_history()