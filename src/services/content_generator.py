from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from src.clients.gigachat import GigaChatModel


class ContentGenerator:
    def __init__(self, gigachat_model: GigaChatModel):
        self.model = gigachat_model
        self.ngo_info: Optional[Dict[str, Any]] = None

    def set_ngo_info(self, ngo_info: Dict[str, Any]):
        self.ngo_info = ngo_info

    def _build_ngo_context(self) -> str:
        """Формирование контекста об НКО для промпта"""
        if not self.ngo_info:
            return ""

        context_parts = []

        if self.ngo_info.get("name"):
            context_parts.append(f"Название организации: {self.ngo_info['name']}")

        if self.ngo_info.get("activity"):
            context_parts.append(f"Деятельность: {self.ngo_info['activity']}")

        forms = self.ngo_info.get("forms", [])
        if forms:
            forms_list = []
            for form_key in forms:
                if form_key == "other":
                    other_text = self.ngo_info.get("forms_other", "")
                    if other_text:
                        forms_list.append(other_text)
                else:
                    forms_list.append(form_key)
            if forms_list:
                context_parts.append(f"Формы деятельности: {', '.join(forms_list)}")

        if self.ngo_info.get("region"):
            context_parts.append(f"Регион работы: {self.ngo_info['region']}")

        if context_parts:
            return "\n".join(context_parts)
        return ""

    async def generate_free_text_post(
        self,
        user_idea: str,
        style: str = "тёплый и человечный",
        additional_info: Optional[str] = None,
    ) -> str:
        ngo_context = self._build_ngo_context()

        system_prompt = f"""Ты - профессиональный SMM-специалист для некоммерческих организаций.

        {ngo_context if ngo_context else "Организация: информация не предоставлена"}

        🎯 ГЛАВНОЕ ПРАВИЛО:
        Используй ТОЛЬКО факты из описания пользователя. Не придумывай:
        - Конкретные цифры и суммы (если не указаны)
        - Имена людей (если не названы)
        - Точные даты и время (если не даны)
        - Детали событий (если не описаны)
        - Результаты и последствия (если не упомянуты)

        ✅ ЧТО МОЖНО:
        - Добавлять эмоциональную окраску к ИМЕЮЩИМСЯ фактам
        - Структурировать информацию для читаемости
        - Добавлять уместные призывы к действию
        - Использовать метафоры и сравнения БЕЗ конкретных деталей

        📝 ПРИЗНАКИ ХОРОШЕГО ПОСТА:
        1. Конкретность: если есть детали - используй их полностью
        2. Визуализация: помоги читателю представить ситуацию
        3. История, не отчёт: покажи процесс, не только результат
        4. Человечность: фокус на людях и их историях (если упомянуты)
        5. Прозрачность: что → как → зачем → что дальше
        6. Естественный призыв: не навязчиво, как продолжение мысли

        📐 СТРУКТУРА:
        • Сильное начало (вопрос/факт/интрига) - 1 предложение
        • Основная часть (раскрытие темы) - 2-3 коротких абзаца по 2-3 предложения
        • Детали/процесс (если есть) - список или абзац
        • Завершение (вывод/призыв/благодарность) - 1-2 предложения
        • Хештеги: 2-4 релевантных

        🎨 СТИЛЬ: {style}

        ⚙️ ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:
        - Длина (в словах): 150-350 слов
        - Длина (в символах): 1000 символов max
        - Эмодзи: 1-2 штуки (в начале разделов или для акцентов)
        - Абзацы: 2-3 предложения max
        - Списки: если есть перечисление (✅ ✓ • →)
        - Хештеги: в конце, с # и названием организации
        - Без воды, канцеляризмов, штампов
        - Живой разговорный язык, но грамотный

        ❌ ИЗБЕГАЙ:
        - "Спешим сообщить" (канцелярит)
        - Избыточных восклицательных знаков!!!
        - Пафоса и манипуляций
        - Общих фраз типа "мы меняем мир"
        """

        prompt = f"""Создай пост для соцсети, который хочется прочитать до конца.

        ИСХОДНАЯ ИДЕЯ:
        {user_idea}

        {f"ДОПОЛНИТЕЛЬНО: {additional_info}" if additional_info else ""}

        ВАЖНО: 
        Работай только с этой информацией. Если деталей мало - сделай короткий ёмкий пост.
        Если деталей много - раскрой их структурированно.

        НЕ ДОДУМЫВАЙ конкретику. Твоя задача - взять ЭТИ факты и подать их интересно."""
        return await self.model.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.7
        )

    async def generate_structured_post(
        self,
        event_type: str,
        date: str,
        location: str,
        participants: str,
        details: str,
        style: str = "разговорный",
    ) -> str:
        """
        Генерация структурированного поста по шаблону

        Args:
            event_type: Тип события
            date: Дата события
            location: Место проведения
            participants: Кто приглашён
            details: Дополнительные детали
            style: Стиль текста

        Returns:
            Готовый пост
        """
        ngo_context = self._build_ngo_context()

        system_prompt = f"""Ты - профессиональный SMM-специалист для некоммерческих организаций.
Создавай посты на основе структурированной информации.

{ngo_context if ngo_context else "Организация: информация не предоставлена"}
        Требования:
        - Стиль: {style}
        - Логичная структура с ключевой информацией
        - Привлекательный заголовок или первая строка
        - 2-3 релевантных хештега"""

        prompt = f"""Создай анонс мероприятия на основе следующей информации:

        Тип события: {event_type}
        Дата: {date}
        Место: {location}
        Участники: {participants}
        Дополнительные детали: {details}

        Создай привлекательный пост-анонс."""

        return await self.model.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.7
        )

    async def generate_structured_form_post(
        self,
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
        """
        Генерация поста на основе структурированной формы (10 вопросов)

        Args:
            event: О каком событии пост
            description: Описание события подробнее
            goal: Главная цель поста
            date: Дата и время (опционально)
            location: Место проведения (опционально)
            platform: Площадка публикации
            audience: Целевая аудитория
            style: Стиль текста
            length: Объём текста
            additional_info: Дополнительная информация (опционально)

        Returns:
            Готовый пост
        """
        ngo_context = self._build_ngo_context()

        # Маппинг стилей
        style_map = {
            "warm": "тёплый и человечный",
            "facts": "с фактами и цифрами",
            "simple": "простой и понятный",
            "formal": "официальный",
            "emotional": "эмоциональный и вдохновляющий",
        }
        style_text = style_map.get(style, "тёплый и человечный")

        # Маппинг объёмов
        length_map = {
            "short": "короткий (100-150 слов) 1000 символов max",
            "medium": "средний (200-300 слов) 1000 символов max",
            "long": "подробный (350-500 слов) 1000 символов max",
        }
        length_text = length_map.get(length, "средний (200-300 слов) 1000 символов max")

        # Маппинг платформ
        platform_map = {
            "telegram": "Telegram",
            "vk": "ВКонтакте",
            "universal": "универсально (для всех платформ)",
        }
        platform_text = platform_map.get(platform, "универсально")

        # Маппинг аудиторий
        audience_map = {
            "locals": "местные жители",
            "youth": "молодёжь",
            "donors": "доноры",
            "volunteers": "волонтёры",
            "media": "СМИ",
            "broad": "широкая аудитория",
        }
        audience_text = audience_map.get(audience, "широкая аудитория")

        # Маппинг целей
        # goal может быть в формате "struct_goal:result" или "other:текст"
        goal_map = {
            "result": "показать результат работы",
            "volunteers": "привлечь волонтёров",
            "donations": "собрать пожертвования",
            "work": "рассказать о работе организации",
            "thanks": "выразить благодарность",
            "announcement": "анонсировать событие",
        }

        # Если цель начинается с "other:", берем текст после двоеточия
        if goal.startswith("other:"):
            goal_text = goal.split(":", 1)[1] if ":" in goal else goal
        elif ":" in goal:
            # Формат "struct_goal:result" - берем часть после двоеточия
            goal_value = goal.split(":")[1]
            goal_text = goal_map.get(goal_value, goal_value)
        else:
            # Если нет двоеточия, проверяем напрямую
            goal_text = goal_map.get(goal, goal)

        system_prompt = f"""Ты - профессиональный SMM-специалист для некоммерческих организаций.
        Создавай качественные посты на основе структурированной информации.
        
        {ngo_context if ngo_context else "Организация: информация не предоставлена"}
        
        🎯 ГЛАВНОЕ ПРАВИЛО:
        Используй ТОЛЬКО факты из описания пользователя. Не придумывай:
        - Конкретные цифры и суммы (если не указаны)
        - Имена людей (если не названы)
        - Точные даты и время (если не даны)
        - Детали событий (если не описаны)
        - Результаты и последствия (если не упомянуты)
        
        ✅ ЧТО МОЖНО:
        - Добавлять эмоциональную окраску к ИМЕЮЩИМСЯ фактам
        - Структурировать информацию для читаемости
        - Добавлять уместные призывы к действию
        - Использовать метафоры и сравнения БЕЗ конкретных деталей
        
        📐 СТРУКТУРА:
        • Сильное начало (вопрос/факт/интрига) - 1 предложение
        • Основная часть (раскрытие темы) - 2-3 коротких абзаца по 2-3 предложения
        • Детали/процесс (если есть) - список или абзац
        • Завершение (вывод/призыв/благодарность) - 1-2 предложения
        • Хештеги: 2-4 релевантных
        
        ⚙️ ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:
        - Длина: {length_text}
        - Длина (в символах): 1000 символов max
        - Стиль: {style_text}
        - Площадка: {platform_text}
        - Целевая аудитория: {audience_text}
        - Эмодзи: 1-2 штуки (в начале разделов или для акцентов)
        - Абзацы: 2-3 предложения max
        - Списки: если есть перечисление (✅ ✓ • →)
        - Хештеги: в конце, с # и названием организации
        - Без воды, канцеляризмов, штампов
        - Живой разговорный язык, но грамотный
        
        ❌ ИЗБЕГАЙ:
        - "Спешим сообщить" (канцелярит)
        - Избыточных восклицательных знаков!!!
        - Пафоса и манипуляций
        - Общих фраз типа "мы меняем мир"
        """

        prompt_parts = [
            f"СОБЫТИЕ: {event}",
            f"ОПИСАНИЕ: {description}",
            f"ГЛАВНАЯ ЦЕЛЬ ПОСТА: {goal_text}",
        ]

        if date:
            prompt_parts.append(f"ДАТА И ВРЕМЯ: {date}")

        if location:
            prompt_parts.append(f"МЕСТО ПРОВЕДЕНИЯ: {location}")

        if additional_info:
            prompt_parts.append(f"ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ: {additional_info}")

        prompt = f"""Создай пост для соцсети на основе следующей структурированной информации:

        {chr(10).join(prompt_parts)}
        
        ВАЖНО:
        - Работай только с этой информацией
        - Учитывай цель поста: {goal_text}
        - Адаптируй стиль под целевую аудиторию: {audience_text}
        - Учитывай особенности платформы: {platform_text}
        - Соблюдай объём: {length_text}
        - Используй стиль: {style_text}
        
        НЕ ДОДУМЫВАЙ конкретику. Твоя задача - взять ЭТИ факты и подать их интересно."""

        return await self.model.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.7
        )

    async def generate_post_from_example(
        self, example_post: str, new_topic: str, style: Optional[str] = None
    ) -> str:
        """
        Генерация поста на основе примера

        Args:
            example_post: Пример готового поста
            new_topic: Новая тема для поста
            style: Стиль (если None, берётся из примера)

        Returns:
            Готовый пост
        """
        ngo_context = self._build_ngo_context()

        system_prompt = f"""Ты - профессиональный SMM-специалист для некоммерческих организаций.

        {ngo_context if ngo_context else "Организация: информация не предоставлена"}

        Твоя задача - создать новый пост, используя стиль и структуру примера."""

        prompt = f"""Вот пример поста, который нам нравится:

        {example_post}

        Создай аналогичный пост на следующую тему: {new_topic}

        {f"Используй стиль: {style}" if style else "Сохрани стиль примера"}

        Новый пост должен иметь такую же структуру и энергетику, но с новым содержанием."""

        return await self.model.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.75
        )

    @staticmethod
    def _parse_edit_response(response: str) -> tuple[str, list[str], list[str]]:
        """
        Парсит ответ нейросети в структурированный формат

        Args:
            response: Сырой ответ от нейросети

        Returns:
            Tuple[edited_text, errors, recommendations]
        """
        result = {"edited_text": "", "errors": [], "recommendations": []}

        current_section = None
        lines = response.replace("\r", "").split("\n")

        for line in lines:
            stripped = line.strip()

            # переключение между секциями
            if stripped == "ИСПРАВЛЕННЫЙ ТЕКСТ:":
                current_section = "edited_text"
                continue
            if stripped == "НАЙДЕННЫЕ ОШИБКИ:":
                current_section = "errors"
                continue
            if stripped == "РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:":
                current_section = "recommendations"
                continue

            # пустая строка
            if stripped == "":
                if current_section == "edited_text":
                    result["edited_text"] += "\n"
                continue

            # наполнение секций
            if current_section == "edited_text":
                result["edited_text"] += line + "\n"

            elif current_section == "errors":
                if "ошибок не обнаружено" in stripped.lower():
                    result["errors"] = []
                else:
                    result["errors"].append(stripped)

            elif current_section == "recommendations":
                result["recommendations"].append(stripped)

        result["edited_text"] = result["edited_text"].strip()

        return (result["edited_text"], result["errors"], result["recommendations"])

    async def edit_post(
        self, original_post: str, edit_request: str
    ) -> tuple[str, list[str], list[str]]:
        """
        Редактирование поста на основе запроса пользователя

        Args:
            original_post: Исходный текст поста
            edit_request: Запрос пользователя на изменение

        Returns:
            Tuple[edited_text, errors, recommendations]
        """
        ngo_context = self._build_ngo_context()

        system_prompt = f"""Ты - редактор SMM-постов для НКО.

        {ngo_context if ngo_context else ""}

        ТВОЯ ЗАДАЧА:
        Отредактировать пост на основе запроса пользователя, который содержит РЕАЛЬНУЮ информацию.
        Выполняй строго по этим правилам. Основанием для любых изменений служат только ИСХОДНЫЙ ПОСТ 
        и ЗАПРОС ПОЛЬЗОВАТЕЛЯ. Дополнительные источники не использовать. 
        Если присутствует ngo_context, его можно учитывать как контекст, но не добавлять фактов.
        
        ИНСТРУКЦИЯ (выполнять строго по порядку):
        1. Проанализируй найденные ошибки ИСКЛЮЧИТЕЛЬНО В ИСХОДНОМ ПОСТЕ. 
        Категории ошибок: ГРАММАТИКА, ОРФОГРАФИЯ, ЛОГИКА, РЕЧЬ (стилистика, словесная выразительность). 
        Для каждой ошибки укажи категорию, краткое описание или фрагмент, что было изменено и почему (как исправлено).
        2. Добавь в текст всю информацию из запроса пользователя; ничего из запроса не игнорировать.
        3. Если исходный пост содержит похожую, но отличающуюся информацию — ЗАМЕНИ её на информацию из запроса.
        4. Сохрани тон, структуру и форматирование исходного поста, если пользователь явно не требует изменений.
        5. Сделай текст естественным и читабельным (короткие предложения, логичные связки).
        6. Дай минимум 2 конкретные и применимые рекомендации по улучшению ОТРЕДАКТИРОВАННОГО ТЕКСТА (версии, полученной после правок ИИ) 
        Рекомендации не должны содержать новых фактов; они могут предлагать конкретные правки фраз, 
        перестановки, сокращения, добавление/удаление эмодзи, изменение призыва к действию, 
        хештегов, форматирования и т.п. 
        Каждая рекомендация должна быть реализуемой — по возможности с кратким примером.
        
        Жёсткие ограничения:
        - Никаких дополнительных разделов, объяснений или мета-комментариев вне указанного формата.
        - Не добавлять фактов, отсутствующих в запросе и исходном посте.
        - Всегда возвращать все три раздела в заявленном формате.
        - Все части ответа на русском языке.
        
        ДАЙ ОТВЕТ СТРОГО В ТАКОМ ФОРМАТЕ:
        
        ИСПРАВЛЕННЫЙ ТЕКСТ:
        [отредактированный текст — только текст поста]
        
        НАЙДЕННЫЕ ОШИБКИ:
        1. [КАТЕГОРИЯ: ГРАММАТИКА] [фрагмент или описание] — [как исправлено и почему]
        2. [КАТЕГОРИЯ: ОРФОГРАФИЯ] [фрагмент или описание] — [как исправлено и почему]
        (Каждая ошибка отдельным пунктом, нужно перечислить ОБЯЗАТЕЛЬНО ВСЕ ошибки)
        
        РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:
        1. [конкретная правка или пример как можно улучшить; без новых фактов]
        2. [конкретная правка или пример как можно улучшить; без новых фактов]
        3. [конкретная правка или пример как можно улучшить; без новых фактов]
        (Всегда минимум 2 рекомендации)
        """

        prompt = f"""Отредактируй пост на основе запроса пользователя.

        ИСХОДНЫЙ ПОСТ:
        {original_post}

        ЗАПРОС ПОЛЬЗОВАТЕЛЯ (содержит реальную информацию):
        {edit_request}
        """

        raw_response = await self.model._generate_text_raw(
            prompt=prompt, system_prompt=system_prompt, temperature=0.0
        )
        return self._parse_edit_response(raw_response)

    async def generate_content_plan(
        self, duration_days: int, posts_per_week: int, preferences: Optional[str] = None
    ) -> str:
        """
        Создание контент-плана

        Args:
            duration_days: Длительность плана в днях
            posts_per_week: Количество постов в неделю
            preferences: Предпочтения по темам/форматам

        Returns:
            Текстовый контент-план
        """
        ngo_context = self._build_ngo_context()

        system_prompt = f"""Ты - опытный SMM-стратег для НКО.
                Создаёшь контент-планы, основываясь СТРОГО на данных организации.

                {ngo_context if ngo_context else "Данные организации не предоставлены - используй общие рекомендации для НКО"}

                ВАЖНО:
                - Все темы постов должны соответствовать деятельности этой конкретной организации
                - НЕ придумывай активности, которых нет в описании
                - Опирайся на указанные формы деятельности и регион работы
                - Предлагай типовые темы, а не конкретные события
                - Используй только HTML-теги, поддерживаемые Telegram: <b>, <strong>, <i>, <em>, <u>, <ins>, <s>, <strike>, <del>, <code>, <pre>, <a href="...">, <tg-spoiler>, <blockquote>
                - НЕ используй тег <br> - используй обычные переносы строк
                - Не добавляй другие теги и не используй Markdown"""

        # Правильно рассчитываем количество постов
        full_weeks = duration_days // 7
        extra_days = duration_days % 7

        # Посты за полные недели
        posts_full_weeks = full_weeks * posts_per_week

        # Посты за оставшиеся дни (пропорционально)
        posts_extra_days = (
            round(extra_days * posts_per_week / 7) if extra_days > 0 else 0
        )

        # Общее количество постов
        total_posts = posts_full_weeks + posts_extra_days

        # Генерируем конкретные даты для постов
        start_date = datetime.now()
        post_dates = []

        # Времена публикаций (можно настроить)
        posting_times = ["10:00", "14:00", "18:00", "12:00", "16:00", "20:00", "11:00"]

        if total_posts > 0:
            # Распределяем посты равномерно по дням
            interval = duration_days / total_posts

            for i in range(total_posts):
                post_day = start_date + timedelta(days=int(i * interval))
                day_name = post_day.strftime("%a").upper()
                day_names = {
                    "MON": "ПН",
                    "TUE": "ВТ",
                    "WED": "СР",
                    "THU": "ЧТ",
                    "FRI": "ПТ",
                    "SAT": "СБ",
                    "SUN": "ВС",
                }

                post_dates.append(
                    {
                        "day_name": day_names.get(day_name, day_name),
                        "date": post_day.strftime("%d.%m"),
                        "time": posting_times[i % len(posting_times)],
                        "week": (post_day - start_date).days // 7 + 1,
                    }
                )

        # Формируем структуру с готовыми датами
        posts_structure = ""
        current_week = 0

        for idx, post_date in enumerate(post_dates, 1):
            if post_date["week"] != current_week:
                current_week = post_date["week"]
                week_posts_count = sum(
                    1 for p in post_dates if p["week"] == current_week
                )
                posts_structure += f"\n<b>📅 Неделя {current_week}</b> ({week_posts_count} {'пост' if week_posts_count == 1 else 'постов'})\n\n"

            posts_structure += f"<b>{post_date['day_name']} {post_date['date']}, {post_date['time']}</b>\n"
            posts_structure += "[ЗАПОЛНИ: Тип поста (📝/❤️/📊/🤝/🙏/📅)]\n"
            posts_structure += (
                "Тема: [ЗАПОЛНИ тему, связанную с деятельностью организации]\n"
            )
            posts_structure += "Формат: Текст + фото\n\n"

            if idx < len(post_dates):
                posts_structure += "---\n\n"

        prompt = f"""Составь контент-план для Telegram-канала НКО.

        📊 ПАРАМЕТРЫ:
        - Период: {duration_days} дней
        - Частота: {posts_per_week} постов в неделю
        - ИТОГО ПОСТОВ: {total_posts}
        {f"- Пожелания: {preferences}" if preferences else ""}

        ⚠️ КРИТИЧЕСКИ ВАЖНО:
        КОЛИЧЕСТВО ПОСТОВ СТРОГО ФИКСИРОВАНО: {total_posts} {"пост" if total_posts == 1 else "постов"}
        НЕ ДОБАВЛЯЙ больше постов! НЕ УДАЛЯЙ посты!
        Даты и время УЖЕ РАССЧИТАНЫ - только заполни темы!

        ТИПЫ КОНТЕНТА (выбирай подходящие):
        📢 Информационные - объяснение направлений работы, факты, статистика
        ❤️ Эмоциональные - истории помощи, результаты работы
        📊 Прозрачность - отчёты, цифры, достижения
        🤝 Вовлечение - вопросы, обсуждения, призывы
        🙏 Признательность - благодарности волонтёрам и партнёрам
        📅 Актуальное - анонсы, новости, наборы

        📋 СТРУКТУРА ПЛАНА (ЗАПОЛНИ ТЕМЫ):

        {posts_structure}

        ЗАДАЧА:
        1. Замени "[ЗАПОЛНИ: Тип поста]" на подходящий тип с эмодзи И полным названием (например: "📅 Актуальное - анонсы, новости, наборы" или "❤️ Эмоциональные - истории помощи, результаты работы")
        2. Замени "[ЗАПОЛНИ тему...]" на конкретную тему, связанную с деятельностью организации
        3. НЕ МЕНЯЙ даты, время и количество постов
        4. НЕ ДОБАВЛЯЙ новые посты
        5. Все темы должны соответствовать профилю НКО
        6. Используй только HTML-теги, поддерживаемые Telegram (перечень выше)
        7. ВАЖНО: Тип поста должен содержать эмодзи и полное описание, а не только эмодзи"""

        return await self.model._generate_text_raw(
            prompt=prompt, system_prompt=system_prompt, temperature=0.6, max_tokens=3000
        )
