from __future__ import annotations

import html
from html.parser import HTMLParser
from typing import Iterable

ALLOWED_TAGS: dict[str, set[str]] = {
    "b": set(),
    "strong": set(),
    "i": set(),
    "em": set(),
    "u": set(),
    "ins": set(),
    "s": set(),
    "strike": set(),
    "del": set(),
    "code": set(),
    "pre": {"language"},
    "a": {"href"},
    "tg-spoiler": set(),
    "blockquote": set(),
}

SELF_CLOSING_TAGS: set[str] = set()  # Telegram не поддерживает самозакрывающиеся теги


class _TelegramHTMLSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self._result: list[str] = []

    def handle_starttag(self, tag: str, attrs: Iterable[tuple[str, str | None]]):
        if tag in ALLOWED_TAGS:
            self._result.append(f"<{tag}{self._format_attrs(tag, attrs)}>")
        elif tag in SELF_CLOSING_TAGS:
            self._result.append(f"<{tag}>")

    def handle_endtag(self, tag: str):
        if tag in ALLOWED_TAGS:
            self._result.append(f"</{tag}>")

    def handle_startendtag(self, tag: str, attrs: Iterable[tuple[str, str | None]]):
        if tag in SELF_CLOSING_TAGS:
            self._result.append(f"<{tag}>")
        elif tag in ALLOWED_TAGS:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_data(self, data: str):
        self._result.append(html.escape(data, quote=False))

    def handle_entityref(self, name: str):
        self._result.append(f"&{name};")

    def handle_charref(self, name: str):
        self._result.append(f"&#{name};")

    def handle_comment(self, data: str):
        # Комментарии Telegram не поддерживает — пропускаем
        pass

    def _format_attrs(self, tag: str, attrs: Iterable[tuple[str, str | None]]) -> str:
        allowed = ALLOWED_TAGS.get(tag, set())
        filtered = [
            (name, value)
            for name, value in attrs
            if name in allowed and value is not None
        ]
        if not filtered:
            return ""
        return "".join(
            f' {name}="{html.escape(value, quote=True)}"' for name, value in filtered
        )

    def get_value(self) -> str:
        return "".join(self._result)


def sanitize_telegram_html(text: str | None) -> str:
    """Удаляет или экранирует неподдерживаемые Telegram HTML-теги."""
    if not text:
        return ""
    # Заменяем <br> и <br/> на перенос строки, так как Telegram не поддерживает этот тег
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    parser = _TelegramHTMLSanitizer()
    parser.feed(text)
    parser.close()
    return parser.get_value()
