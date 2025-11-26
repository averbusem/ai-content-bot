from __future__ import annotations

from aiogram import Bot

from src.services.image_overlay import ImageOverlayOptions, apply_image_overlay

OVERLAY_TYPE_SIZES = {
    "logo": 0.22,
    "photo": 0.5,
}


async def download_file_bytes(bot: Bot, file_id: str) -> bytes:
    """Скачивает файл из Telegram и возвращает его байты."""
    file = await bot.get_file(file_id)
    downloaded = await bot.download_file(file.file_path)
    return downloaded.read()


async def build_image_with_overlay(
    bot: Bot,
    base_file_id: str,
    overlay_file_id: str,
    overlay_type: str,
    position: str,
) -> bytes:
    """Комбинирует исходное изображение с пользовательским логотипом/фото."""
    if overlay_type not in OVERLAY_TYPE_SIZES:
        raise ValueError(f"Unknown overlay type: {overlay_type}")

    base_bytes = await download_file_bytes(bot, base_file_id)
    overlay_bytes = await download_file_bytes(bot, overlay_file_id)
    options = ImageOverlayOptions(
        position=position, size_ratio=OVERLAY_TYPE_SIZES[overlay_type]
    )

    return apply_image_overlay(base_bytes, overlay_bytes, options)
