import re
from typing import List, Dict, Optional


class ContentPlanParser:
    """Парсер контент-плана для извлечения дней."""

    @staticmethod
    def parse_content_plan(content_plan: str) -> List[Dict[str, Optional[str]]]:
        """
        Парсинг контент-плана и извлечение информации о днях.

        Формат контент-плана:
        ПН 01.01, 10:00
        [Тип поста]
        Тема: [тема]
        Формат: [формат]

        Returns:
            Список словарей с информацией о днях
        """
        days = []
        lines = content_plan.split("\n")

        current_day = None
        current_week = 1

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            week_match = re.search(r"Неделя\s+(\d+)", line, re.IGNORECASE)
            if week_match:
                current_week = int(week_match.group(1))
                i += 1
                continue

            day_match = re.search(
                r"<(?:b|strong)>([А-Я]{2})\s+(\d{2}\.\d{2}),\s*(\d{2}:\d{2})</(?:b|strong)>",
                line,
            )
            if day_match:
                if current_day:
                    days.append(current_day)

                day_name = day_match.group(1)
                date = day_match.group(2)
                time = day_match.group(3)

                current_day = {
                    "day_name": day_name,
                    "date": date,
                    "time": time,
                    "post_type": None,
                    "topic": None,
                    "format": None,
                    "week": current_week,
                }
                i += 1
                continue

            # Если есть текущий день, ищем информацию о посте
            if current_day:
                if not current_day["post_type"]:
                    if line and not line.startswith("---") and line != "":
                        if not line.startswith("Тема:") and not line.startswith(
                            "Формат:"
                        ):
                            current_day["post_type"] = line

                topic_match = re.search(r"Тема:\s*(.+)", line, re.IGNORECASE)
                if topic_match:
                    current_day["topic"] = topic_match.group(1).strip()

                format_match = re.search(r"Формат:\s*(.+)", line, re.IGNORECASE)
                if format_match:
                    current_day["format"] = format_match.group(1).strip()

            i += 1

        if current_day:
            days.append(current_day)

        return days

    @staticmethod
    def generate_plan_name(duration_days: int, posts_per_week: int) -> str:
        """Генерирует название контент-плана."""
        return f"Контент-план на {duration_days} дней ({posts_per_week} постов/нед)"
