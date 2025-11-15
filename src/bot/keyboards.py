from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="📝 Генерация текста", callback_data="menu:text_generation"))
    builder.add(InlineKeyboardButton(text="🎨 Генерация картинки", callback_data="menu:image_generation"))
    builder.add(InlineKeyboardButton(text="✏️ Редактор текста", callback_data="menu:text_editor"))
    builder.add(InlineKeyboardButton(text="📅 Контент-план", callback_data="menu:content_plan"))
    builder.add(InlineKeyboardButton(text="⚙️ Рассказать об НКО", callback_data="menu:nko_data"))
    builder.add(InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"))
    
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="menu:main"))
    
    return builder.as_markup()

