from typing import Optional
from .models.gigachat import GigaChatModel


IMAGE_GENERATION_SYSTEM_PROMPT = """ПРАВИЛА КОМПОЗИЦИИ:

- Главный объект в фокусе, чёткий и резкий

- Естественные непринуждённые позы, избегать скованности и неестественности

- Правильная анатомия человека: ровно 5 пальцев на каждой руке, пропорциональное тело

- Разнообразие: разный возраст, национальности, особенности

- Искренние эмоции: настоящие выражения лиц, живые моменты

- Чистый фон: не загромождённый, дополняет главный объект

- Подходящее освещение: естественное, ровное, создаёт глубину

ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ:

- Разрешение: высокое качество, подходит для социальных сетей

- Соотношение сторон: 1:1 (квадратный формат для универсального использования)

- Формат: чёткий, профессиональный, готовый к печати

- Фокус: резкий на главном объекте, допустимо лёгкое размытие фона

ОБЯЗАТЕЛЬНЫЕ ПРОВЕРКИ:

✓ У всех людей правильная анатомия (5 пальцев, 2 руки, 2 ноги)

✓ Лица чёткие и хорошо прорисованы

✓ Текст (если есть) читаемый и без ошибок

✓ Освещение равномерное по всему изображению

✓ Нет искажений и артефактов

✓ Изображение рассказывает понятную историю

✓ Уважительное и достойное изображение людей

ИЗБЕГАТЬ:

✗ Стереотипных или жалостливых образов

✗ Слишком постановочных или фальшивых сцен

✗ Грустной или депрессивной атмосферы (если специально не запрошено)

✗ Детей в уязвимых или недостойных ситуациях

✗ Загромождённых или запутанных композиций

✗ Плохо читаемого текста или неразборчивых шрифтов

✗ Анатомических ошибок (лишние пальцы, искажённые конечности)"""


class ImageGenerator:
    def __init__(self, gigachat_model: GigaChatModel):
        self.model = gigachat_model

    def build_image_prompt(self, description: str, style: str, colors: str) -> str:
        """Сборка промпта для генерации изображения на основе параметров пользователя"""
        
        style_descriptions = {
            "realistic": "реалистичное фото, фотографический стиль, высокая детализация",
            "illustration": "иллюстрация, рисунок, художественный стиль",
            "minimalism": "минималистичный стиль, простые формы, чистые линии",
            "poster": "постер, афиша, графический дизайн, привлекательный визуал",
            "business": "деловой стиль, профессиональный вид, корпоративный дизайн"
        }
        
        color_descriptions = {
            "warm": "тёплые цвета: красный, оранжевый, жёлтый",
            "cold": "холодные цвета: синий, голубой, зелёный",
            "bright": "яркие и контрастные цвета",
            "neutral": "нейтральные и пастельные тона",
            "auto": ""  # ИИ сам подберёт цвета
        }
        
        prompt_parts = [description]
        
        style_desc = style_descriptions.get(style, "")
        if style_desc:
            prompt_parts.append(f"Стиль: {style_desc}")
        
        color_desc = color_descriptions.get(colors, "")
        if color_desc:
            prompt_parts.append(f"Цветовая палитра: {color_desc}")
        
        return ", ".join(prompt_parts)

    async def generate_image_prompt(
            self,
            post_text: str,
            image_description: Optional[str] = None
    ) -> str:
        """
        Генерация промпта для создания изображения на основе текста поста

        Args:
            post_text: Текст поста
            image_description: Дополнительное описание желаемого изображения

        Returns:
            Промпт для генерации изображения
        """
        system_prompt = """Ты - специалист по созданию промптов для генерации изображений.
Создавай детальные описания для AI, которые помогут создать качественную картинку для поста НКО."""

        prompt = f"""На основе следующего текста поста создай детальный промпт для генерации изображения.

Текст поста:
{post_text}

{f"Дополнительные пожелания: {image_description}" if image_description else ""}

Промпт должен:
- Быть на русском языке
- Содержать описание стиля (реалистичный, иллюстрация, минималистичный и т.д.)
- Описывать композицию и настроение
- Быть релевантным теме НКО и социальной направленности
- Не содержать текста на изображении

Создай промпт длиной 50-150 слов."""

        return await self.model.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )

    async def generate_image(
            self,
            prompt: str,
            width: int = 1024,
            height: int = 1024
    ) -> bytes:
        """
        Генерация изображения по промпту

        Args:
            prompt: Промпт для генерации изображения
            width: Ширина изображения
            height: Высота изображения

        Returns:
            Байты изображения
        """
        return await self.model.generate_image(
            prompt=prompt,
            system_prompt=IMAGE_GENERATION_SYSTEM_PROMPT,
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
        """
        Генерация изображения на основе параметров пользователя

        Args:
            description: Описание изображения
            style: Стиль изображения
            colors: Цветовая палитра
            width: Ширина изображения
            height: Высота изображения

        Returns:
            Байты изображения
        """
        prompt = self.build_image_prompt(description, style, colors)
        return await self.generate_image(prompt, width, height)

    async def generate_image_from_post(
            self,
            post_text: str,
            image_description: Optional[str] = None,
            width: int = 1024,
            height: int = 1024
    ) -> bytes:
        """
        Генерация изображения на основе текста поста

        Args:
            post_text: Текст поста
            image_description: Дополнительное описание желаемого изображения
            width: Ширина изображения
            height: Высота изображения

        Returns:
            Байты изображения
        """
        prompt = await self.generate_image_prompt(post_text, image_description)
        return await self.generate_image(prompt, width, height)

