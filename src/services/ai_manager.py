from typing import Optional, Dict, Any
from .models.gigachat import GigaChatModel
from .models.salute import SaluteSpeechModel
from .content_generator import ContentGenerator


class AIManager:
    def __init__(self):
        # Инициализация GigaChat
        self.gigachat = GigaChatModel()

        # Инициализация Salute Speech
        self.salute_speech = SaluteSpeechModel()

        # Инициализация генератора контента
        self.content_generator = ContentGenerator(self.gigachat)

        # Хранилище информации об НКО для каждого пользователя
        self.user_ngo_info: Dict[int, Dict[str, Any]] = {}

    def set_user_ngo_info(self, user_id: int, ngo_info: Dict[str, Any]):
        self.user_ngo_info[user_id] = ngo_info
        self.content_generator.set_ngo_info(ngo_info)

    def get_user_ngo_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.user_ngo_info.get(user_id)

    # === МЕТОДЫ ДЛЯ РАБОТЫ С ТЕКСТОМ ===

    async def generate_free_text_post(
        self,
        user_id: int,
        user_idea: str,
        style: str = "разговорный",
        additional_info: Optional[str] = None
    ) -> str:
        """Генерация свободного текста поста"""
        # Устанавливаем контекст НКО если есть
        if user_id in self.user_ngo_info:
            self.content_generator.set_ngo_info(self.user_ngo_info[user_id])
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
        if user_id in self.user_ngo_info:
            self.content_generator.set_ngo_info(self.user_ngo_info[user_id])
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

    async def generate_post_from_example(
        self,
        user_id: int,
        example_post: str,
        new_topic: str,
        style: Optional[str] = None
    ) -> str:
        """Генерация поста на основе примера"""
        if user_id in self.user_ngo_info:
            self.content_generator.set_ngo_info(self.user_ngo_info[user_id])
        else:
            self.content_generator.ngo_info = None

        return await self.content_generator.generate_post_from_example(
            example_post=example_post,
            new_topic=new_topic,
            style=style
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
        """Создание контент-плана !!! ДОРАБОТАТЬ !!!"""
        if user_id in self.user_ngo_info:
            self.content_generator.set_ngo_info(self.user_ngo_info[user_id])
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
        return await self.gigachat.generate_image(
            prompt=prompt,
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
        # Сначала создаём промпт
        image_prompt = await self.content_generator.generate_image_prompt(
            post_text=post_text,
            image_description=image_description
        )

        # Затем генерируем изображение
        return await self.gigachat.generate_image(
            prompt=image_prompt,
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