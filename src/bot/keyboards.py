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


def nko_forms_keyboard(selected_forms: list = None) -> InlineKeyboardMarkup:
    if selected_forms is None:
        selected_forms = []
    
    builder = InlineKeyboardBuilder()
    
    forms = [
        ("🎯 Проекты", "forms:projects"),
        ("🎪 Мероприятия", "forms:events"),
        ("💰 Сбор пожертвований", "forms:donations"),
        ("🤝 Волонтёрство", "forms:volunteering"),
        ("📚 Образование", "forms:education"),
        ("🏥 Адресная помощь", "forms:direct_help"),
        ("📢 Информационная работа", "forms:info_work"),
        ("✏️ Другое", "forms:other"),
    ]
    
    for text, callback_data in forms:
        is_selected = callback_data.split(":")[1] in selected_forms
        prefix = "✅ " if is_selected else ""
        builder.add(InlineKeyboardButton(
            text=f"{prefix}{text}",
            callback_data=callback_data
        ))
    
    builder.adjust(2)
    
    if selected_forms:
        builder.add(InlineKeyboardButton(text="➡️ Далее", callback_data="nko_forms:next"))
    
    builder.add(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back"))
    
    return builder.as_markup()


def nko_skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="⏭️ Пропустить", callback_data="nko_skip:skip"))
    builder.add(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back"))
    
    builder.adjust(1)
    return builder.as_markup()


def text_generation_method_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="💬 Свободный текст", callback_data="text_gen:free_text"))
    builder.add(InlineKeyboardButton(text="📋 Структурированная форма", callback_data="text_gen:struct"))
    builder.add(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back"))
    
    builder.adjust(1)
    return builder.as_markup()


def text_generation_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="✅ Всё отлично, спасибо!", callback_data="text_result:ok"))
    builder.add(InlineKeyboardButton(text="✏️ Изменить", callback_data="text_result:edit"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu:back"))
    
    builder.adjust(1)
    return builder.as_markup()
