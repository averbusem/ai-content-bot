from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="📝 Генерация текста", callback_data="main_menu:text_generation"))
    builder.add(InlineKeyboardButton(text="🎨 Генерация картинки", callback_data="main_menu:image_generation"))
    builder.add(InlineKeyboardButton(text="✏️ Редактор текста", callback_data="main_menu:text_editor"))
    builder.add(InlineKeyboardButton(text="📅 Контент-план", callback_data="main_menu:content_plan"))
    builder.add(InlineKeyboardButton(text="⚙️ Рассказать об НКО", callback_data="main_menu:nko_data"))
    builder.add(InlineKeyboardButton(text="❓ Помощь", callback_data="main_menu:help"))
    
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back"))
    
    return builder.as_markup()


def nko_data_empty_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="📝 Заполнить данные", callback_data="nko_menu:fill_data"))
    builder.add(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back"))
    
    builder.adjust(1)
    return builder.as_markup()


def nko_data_exists_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="✏️ Изменить данные", callback_data="nko_menu:edit_data"))
    builder.add(InlineKeyboardButton(text="🗑️ Удалить данные", callback_data="nko_menu:delete_data"))
    builder.add(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back"))
    
    builder.adjust(1)
    return builder.as_markup()

