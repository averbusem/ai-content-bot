from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Literal

from PIL import Image


OverlayPosition = Literal[
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
    "center",
]


@dataclass
class ImageOverlayOptions:
    """Настройки добавления пользовательского изображения поверх сгенерированного."""

    position: OverlayPosition = "bottom_right"
    size_ratio: float = 0.25
    padding_ratio: float = 0.035
    opacity: float = 1.0


def apply_image_overlay(
    base_image_bytes: bytes,
    overlay_image_bytes: bytes,
    options: ImageOverlayOptions | None = None,
) -> bytes:
    """
    Накладывает пользовательское изображение (логотип/фото) поверх базовой картинки.

    Args:
        base_image_bytes: Исходное изображение
        overlay_image_bytes: Изображение, которое нужно добавить
        options: Настройки размещения

    Returns:
        Байты изображения с добавленным оверлеем
    """

    cfg = options or ImageOverlayOptions()

    base_image = Image.open(io.BytesIO(base_image_bytes)).convert("RGBA")
    overlay_image = Image.open(io.BytesIO(overlay_image_bytes)).convert("RGBA")

    # Масштабируем логотип/фото относительно ширины базового изображения
    target_width = max(1, int(base_image.width * min(max(cfg.size_ratio, 0.05), 1.0)))
    scale = target_width / overlay_image.width
    target_height = max(1, int(overlay_image.height * scale))
    resized_overlay = overlay_image.resize((target_width, target_height), Image.LANCZOS)

    if cfg.opacity < 1.0:
        alpha = resized_overlay.split()[-1]
        alpha = alpha.point(lambda p: int(p * max(min(cfg.opacity, 1.0), 0.1)))
        resized_overlay.putalpha(alpha)

    padding = int(min(base_image.size) * max(cfg.padding_ratio, 0))

    positions = {
        "top_left": (padding, padding),
        "top_right": (
            base_image.width - resized_overlay.width - padding,
            padding,
        ),
        "bottom_left": (
            padding,
            base_image.height - resized_overlay.height - padding,
        ),
        "bottom_right": (
            base_image.width - resized_overlay.width - padding,
            base_image.height - resized_overlay.height - padding,
        ),
        "center": (
            (base_image.width - resized_overlay.width) // 2,
            (base_image.height - resized_overlay.height) // 2,
        ),
    }

    origin = positions.get(cfg.position, positions["bottom_right"])
    x = max(0, min(origin[0], base_image.width - resized_overlay.width))
    y = max(0, min(origin[1], base_image.height - resized_overlay.height))

    composed = base_image.copy()
    composed.alpha_composite(resized_overlay, dest=(x, y))

    output = io.BytesIO()
    output_format = base_image.format or "PNG"

    if output_format.upper() == "JPEG":
        composed.convert("RGB").save(output, format=output_format, quality=95)
    else:
        composed.save(output, format=output_format)

    return output.getvalue()
