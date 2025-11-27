import re
import html
from typing import Optional


def markdown_to_html(text: Optional[str]) -> str:
    """
    Преобразует Markdown в HTML для Telegram.

    Поддерживает:
    - **текст** / __текст__ -> <b>текст</b>
    - *текст* / _текст_ -> <i>текст</i>
    - ~~текст~~ -> <s>текст</s>
    - `код` -> <code>код</code>
    - ```блок``` -> <pre>блок</pre>
    """
    if not text:
        return ""

    result = html.escape(text)
    placeholders: list[tuple[str, str]] = []

    def save_code(match: re.Match, tag: str) -> str:
        content = match.group(1).strip() if tag == "pre" else match.group(1)
        placeholders.append((content, tag))
        return f"\x00{len(placeholders) - 1}\x00"

    # Сохраняем код
    result = re.sub(
        r"```(.*?)```", lambda m: save_code(m, "pre"), result, flags=re.DOTALL
    )
    result = re.sub(r"`([^`]+)`", lambda m: save_code(m, "code"), result)

    # Форматирование
    patterns = [
        (r"\*\*(.+?)\*\*", r"<b>\1</b>"),
        (r"__(.+?)__", r"<b>\1</b>"),
        (r"~~(.+?)~~", r"<s>\1</s>"),
        (r"(?<!\*)\*(?!\*)([^\*\n]+?)\*(?!\*)", r"<i>\1</i>"),  # без переносов
        (r"(?<!_)_(?!_)([^_\n]+?)_(?!_)", r"<i>\1</i>"),  # без переносов
    ]

    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)

    # Восстанавливаем код
    for i, (content, tag) in enumerate(placeholders):
        result = result.replace(f"\x00{i}\x00", f"<{tag}>{content}</{tag}>")

    return result
