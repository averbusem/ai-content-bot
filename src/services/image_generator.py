from typing import Optional

from .models.gigachat import GigaChatModel
from .text_overlay import TextOverlayConfig, TextOverlayService

IMAGE_GENERATION_SYSTEM_PROMPT = """ПРАВИЛА КОМПОЗИЦИИ:

- Главный объект в фокусе, чёткий и резкий
- Естественные непринуждённые позы, избегать скованности и неестественности
- Правильная анатомия человека: ровно 5 пальцев на каждой руке, пропорциональное тело
- Разнообразие: разный возраст, национальности, особенности
- Искренние эмоции: настоящие выражения лиц, живые моменты
- Чистый фон: не загромождённый, дополняет главный объект
- Подходящее освещение: естественное, ровное, создаёт глубину
- ЗАПРЕЩЕНО писать какой либо текст на изображении

ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ:

- Разрешение: высокое качество, подходит для социальных сетей
- Соотношение сторон: 1:1 (квадратный формат для универсального использования)
- Формат: чёткий, профессиональный, готовый к печати
- Фокус: резкий на главном объекте, допустимо лёгкое размытие фона

ОБЯЗАТЕЛЬНЫЕ ПРОВЕРКИ:

✓ У всех людей правильная анатомия (5 пальцев, 2 руки, 2 ноги)
✓ Лица чёткие и хорошо прорисованы
✓ На изображении НЕТ надписей, букв, логотипов и текстовых элементов
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
✗ Любых надписей, текста, логотипов или мелких буквенных элементов
✗ Анатомических ошибок (лишние пальцы, искажённые конечности)"""

INFO_TEXT_SYSTEM_PROMPT = """Ты — помощник маркетолога НКО.
Твоя задача — составлять короткие и очень информативные текстовые блоки для афиш и постеров.
Строго соблюдай формат: до 4 строк, каждая строка отдельная мысль (название, дата, место, контакт или призыв).
Не используй кавычки и спецсимволы, только понятный текст."""


class ImageGenerator:
    def __init__(
        self,
        gigachat_model: GigaChatModel,
        text_overlay_service: Optional[TextOverlayService] = None
    ):
        self.model = gigachat_model
        self.text_overlay = text_overlay_service

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
            "auto": ""
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
            height: int = 1024,
            overlay_text: Optional[str] = None,
            overlay_font: Optional[str] = None,
            overlay_config: Optional[TextOverlayConfig] = None
    ) -> bytes:
        """
        Генерация изображения по промпту (БЕЗ исходного изображения)

        Args:
            prompt: Промпт для генерации изображения
            width: Ширина изображения
            height: Высота изображения

        Returns:
            Байты изображения
        """
        safe_prompt = f"""{prompt}

Важно: НЕ добавляй текст, надписи, цифры, логотипы, буквы или любые текстовые элементы. На изображении не должно быть слова, фраз или символов."""

        base_image = await self.model.generate_image(
            prompt=safe_prompt,
            system_prompt=IMAGE_GENERATION_SYSTEM_PROMPT,
            width=width,
            height=height
        )
        return self._apply_overlay_if_needed(
            base_image,
            overlay_text,
            overlay_font,
            overlay_config
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
            overlay_config: Optional[TextOverlayConfig] = None
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
        image_bytes = await self.generate_image(prompt, width, height)

        overlay_text = prepared_info_text
        if include_info_block:
            overlay_text = overlay_text or await self.generate_information_text(
                post_text=post_text,
                image_description=image_description
            )

        return self._apply_overlay_if_needed(
            image_bytes,
            overlay_text,
            overlay_font,
            overlay_config
        )

    async def edit_image(
            self,
            source_image_data: bytes,
            edit_request: str,
            width: int = 1024,
            height: int = 1024
    ) -> bytes:
        """
        Редактирование существующего изображения через анализ → генерацию

        Args:
            source_image_data: Байты исходного изображения
            edit_request: Описание требуемых изменений
            width: Ширина результата
            height: Высота результата

        Returns:
            Байты отредактированного изображения
        """
        analysis_prompt = """Подробно опиши это изображение для воссоздания.

Укажи:
1. Основные объекты и персонажи (внешний вид, одежда, позы)
2. Фон и окружение
3. Освещение и атмосферу
4. Цветовую гамму
5. Стиль изображения (фото, рисунок, и т.д.)
6. Композицию

Описание должно быть детальным, но структурированным."""

        image_description = await self.model.analyze_image(
            image_data=source_image_data,
            prompt=analysis_prompt
        )

        generation_prompt = f"""На основе этого описания исходного изображения:

{image_description}

Создай НОВОЕ изображение со следующими изменениями:
{edit_request}

ВАЖНО:
- Сохрани все элементы, которые НЕ упомянуты в изменениях
- Измени ТОЛЬКО то, что явно указано
- Сохрани общий стиль и атмосферу
- Создай целостное изображение

Опиши детально, как должно выглядеть финальное изображение в одном абзаце (50-100 слов)."""

        final_prompt = await self.model.generate_text(
            prompt=generation_prompt,
            temperature=0.5
        )

        return await self.generate_image(
            prompt=final_prompt,
            width=width,
            height=height
        )

    async def generate_information_text(
            self,
            post_text: str,
            image_description: Optional[str] = None
    ) -> str:
        """
        Генерация информационного блока для афиши/постера.
        Возвращает от 1 до 4 строк лаконичного текста.
        """
        prompt = f"""Составь текстовый блок для афиши.
Он должен включать ключевую информацию: название события, дату/время, место или формат участия,
а также краткий призыв или контакт (если это уместно).

Текст поста:
{post_text}

{f"Контекст изображения: {image_description}" if image_description else ""}

Требования:
- до четырёх строк
- без кавычек и лишних пояснений
- каждая строка до 60 символов
- язык: русский.

Верни только сам текст."""

        result = await self.model.generate_text(
            prompt=prompt,
            system_prompt=INFO_TEXT_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=400
        )
        return result.strip()

    def _apply_overlay_if_needed(
            self,
            image_bytes: bytes,
            overlay_text: Optional[str],
            overlay_font: Optional[str],
            overlay_config: Optional[TextOverlayConfig]
    ) -> bytes:
        if not overlay_text or not overlay_text.strip():
            return image_bytes

        if not self.text_overlay:
            return image_bytes

        return self.text_overlay.apply_text(
            image_bytes=image_bytes,
            text=overlay_text,
            font_variant=overlay_font,
            config=overlay_config
        )

    async def create_from_example(
            self,
            example_image_data: bytes,
            creation_request: str,
            width: int = 1024,
            height: int = 1024
    ) -> bytes:
        """
        Создание нового изображения на основе примера через анализ → генерацию

        Args:
            example_image_data: Байты изображения-примера
            creation_request: Описание того, что нужно создать
            width: Ширина результата
            height: Высота результата

        Returns:
            Байты нового изображения
        """
        analysis_prompt = """Проанализируй стиль этого изображения.

Укажи:
1. Художественный стиль (реализм, иллюстрация, минимализм и т.д.)
2. Цветовую палитру и настроение
3. Композицию и компоновку
4. Особенности освещения
5. Общую атмосферу

Опиши стилистику, которую можно применить к другому изображению."""

        style_description = await self.model.analyze_image(
            image_data=example_image_data,
            prompt=analysis_prompt
        )

        generation_prompt = f"""Используя следующий стиль как основу:

{style_description}

Создай новое изображение: {creation_request}

Сохрани стилистику примера, но создай оригинальное содержание.

Опиши детально финальное изображение в одном абзаце (50-100 слов)."""

        final_prompt = await self.model.generate_text(
            prompt=generation_prompt,
            temperature=0.5
        )

        return await self.generate_image(
            prompt=final_prompt,
            width=width,
            height=height
        )