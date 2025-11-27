from __future__ import annotations

import io
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


@dataclass
class TextOverlayConfig:
    """Настройки отображения текста поверх изображения."""

    position: str = "bottom"
    max_width_ratio: float = 0.7
    padding_ratio: float = 0.05
    background_color: Tuple[int, int, int, int] = (0, 0, 0, 210)
    text_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    line_spacing: float = 1.25
    font_size_ratio: float = 0.07
    uppercase_headers: bool = True
    background_expand_ratio: float = 0.2


class TextOverlayService:
    """Сервис для нанесения текста на изображение с поддержкой кириллицы."""

    def __init__(self, font_candidates: Optional[Sequence[str]] = None):
        self._resolved_fonts = self._discover_fonts(font_candidates)
        if not self._resolved_fonts:
            raise RuntimeError(
                "Не найдено ни одного рабочего шрифта с поддержкой кириллицы. "
                "Убедитесь, что папка assets/fonts/ содержит .ttf файлы или установлены системные шрифты."
            )

    def _discover_fonts(
        self, custom_candidates: Optional[Sequence[str]]
    ) -> Dict[str, str]:
        """Ищет доступные шрифты в проекте и системе."""
        candidates = []

        local_fonts_dir = Path(__file__).parent / "fonts"
        assets_fonts_dir = Path(__file__).parent.parent / "assets" / "fonts"

        for fonts_dir in (local_fonts_dir, assets_fonts_dir):
            if fonts_dir.exists() and fonts_dir.is_dir():
                candidates.extend(str(p) for p in fonts_dir.glob("*.ttf"))
                candidates.extend(str(p) for p in fonts_dir.glob("*.ttc"))

        if custom_candidates:
            candidates.extend(custom_candidates)

        resolved = {}
        for path in candidates:
            font_name = Path(path).stem.lower()
            if font_name in resolved:
                continue

            try:
                ImageFont.truetype(path, size=25)
                resolved[font_name] = path
            except Exception:
                continue

        return resolved

    def list_fonts(self) -> List[str]:
        """Возвращает список доступных шрифтов."""
        return list(self._resolved_fonts.keys())

    def _get_font(
        self, size: int, font_variant: Optional[str] = None
    ) -> ImageFont.FreeTypeFont:
        """Загружает шрифт нужного размера."""
        if font_variant:
            key = font_variant.strip().lower()
            path = self._resolved_fonts.get(key)
            if path:
                return ImageFont.truetype(path, size=size)

        # Случайный шрифт из доступных
        path = random.choice(list(self._resolved_fonts.values()))
        return ImageFont.truetype(path, size=size)

    def _wrap_text(
        self,
        text: str,
        draw: ImageDraw.ImageDraw,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> List[str]:
        """Разбивает текст на строки по ширине."""
        lines = []
        for paragraph in text.strip().splitlines():
            paragraph = paragraph.strip()
            if not paragraph:
                lines.append("")
                continue

            words = paragraph.split()
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if draw.textlength(test_line, font=font) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

        return lines

    def apply_text(
        self,
        image_bytes: bytes,
        text: str,
        font_variant: Optional[str] = None,
        config: Optional[TextOverlayConfig] = None,
    ) -> bytes:
        """
        Добавляет текст на изображение.

        Args:
            image_bytes: Исходное изображение
            text: Текст для нанесения
            font_variant: Название шрифта (опционально)
            config: Настройки отображения

        Returns:
            Байты обновлённого изображения
        """
        if not text or not text.strip():
            return image_bytes

        cfg = config or TextOverlayConfig()
        base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        # Расчёт базовых параметров
        max_text_width = int(base_image.width * cfg.max_width_ratio)
        padding = int(min(base_image.size) * cfg.padding_ratio)
        font_size = max(60, int(base_image.height * cfg.font_size_ratio))

        # Создание оверлея
        overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Загрузка шрифта и перенос текста
        font = self._get_font(font_size, font_variant)
        lines = self._wrap_text(text, draw, font, max_text_width)

        if not any(line.strip() for line in lines):
            return image_bytes

        # Расчёт размеров текстового блока
        line_heights = [
            draw.textbbox((0, 0), line or " ", font=font)[3]
            - draw.textbbox((0, 0), line or " ", font=font)[1]
            for line in lines
        ]
        spacing = (
            int(line_heights[0] * max(cfg.line_spacing - 1.0, 0)) if line_heights else 0
        )
        text_height = sum(line_heights) + spacing * max(len(lines) - 1, 0)
        text_width = max(
            (draw.textlength(line, font=font) for line in lines if line), default=0
        )

        # Масштабирование для коротких текстов
        coverage = text_width / max_text_width if max_text_width else 1
        if len(lines) <= 3 and coverage < 0.7:
            scale = min(1.8, max(1.15, 0.9 / max(coverage, 0.05)))
            font = self._get_font(int(font_size * scale), font_variant)
            lines = self._wrap_text(text, draw, font, max_text_width)

            line_heights = [
                draw.textbbox((0, 0), line or " ", font=font)[3]
                - draw.textbbox((0, 0), line or " ", font=font)[1]
                for line in lines
            ]
            spacing = (
                int(line_heights[0] * max(cfg.line_spacing - 1.0, 0))
                if line_heights
                else 0
            )
            text_height = sum(line_heights) + spacing * max(len(lines) - 1, 0)
            text_width = max(
                (draw.textlength(line, font=font) for line in lines if line), default=0
            )

        # Размеры и позиция блока
        extra_width = int(text_width * cfg.background_expand_ratio)
        block_width = text_width + padding * 2 + extra_width
        block_height = text_height + padding * 2

        if cfg.position == "top":
            top = padding
        elif cfg.position == "center":
            top = (base_image.height - block_height) // 2
        else:  # bottom
            top = base_image.height - block_height - padding

        left = (base_image.width - block_width) // 2

        # Рисование фона
        draw.rounded_rectangle(
            [left, top, left + block_width, top + block_height],
            radius=int(padding * 0.4),
            fill=cfg.background_color,
        )

        # Рисование текста
        current_y = top + padding
        for idx, line in enumerate(lines):
            display_line = line.upper() if idx == 0 and cfg.uppercase_headers else line
            line_width = draw.textlength(display_line, font=font)
            x = left + (block_width - line_width) / 2
            draw.text((x, current_y), display_line, font=font, fill=cfg.text_color)
            current_y += line_heights[idx] + spacing

        # Композиция и сохранение
        composed = Image.alpha_composite(base_image, overlay)
        output = io.BytesIO()
        output_format = base_image.format or "PNG"

        if output_format.upper() == "JPEG":
            composed.convert("RGB").save(output, format=output_format, quality=95)
        else:
            composed.save(output, format=output_format)

        return output.getvalue()
