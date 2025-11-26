from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="📝 Создание поста", callback_data="main_menu:text_generation"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🎨 Создание картинки", callback_data="main_menu:image_generation"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="✏️ Редактор текста", callback_data="main_menu:text_editor"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📅 Контент-план", callback_data="main_menu:content_plan"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📆 Запланировать пост", callback_data="main_menu:schedule_post"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="⚙️ Информация о НКО", callback_data="main_menu:nko_data"
        )
    )
    builder.add(InlineKeyboardButton(text="❓ Помощь", callback_data="main_menu:help"))

    builder.adjust(1)
    return builder.as_markup()


def admin_user_management_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="📋 Посмотреть запросы", callback_data="admin_menu:requests"
        )
    )
    builder.add(
        InlineKeyboardButton(text="⛔ Заблокировать", callback_data="admin_menu:block")
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def admin_back_to_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Управление пользователями",
            callback_data="admin_menu:back",
        )
    )
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    return builder.as_markup()


def nko_data_empty_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="📝 Заполнить данные", callback_data="nko_menu:fill_data"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def nko_data_exists_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="✏️ Изменить данные", callback_data="nko_menu:edit_data"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🗑️ Удалить данные", callback_data="nko_menu:delete_data"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

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
        builder.add(
            InlineKeyboardButton(text=f"{prefix}{text}", callback_data=callback_data)
        )

    builder.adjust(2)

    if selected_forms:
        builder.add(
            InlineKeyboardButton(text="➡️ Далее", callback_data="nko_forms:next")
        )

    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    return builder.as_markup()


def nko_skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="nko_skip:skip")
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def text_generation_method_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="💬 Свободный текст", callback_data="text_gen:free_text"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📋 Структурированная форма", callback_data="text_gen:struct"
        )
    )
    builder.add(
        InlineKeyboardButton(text="📝 По примеру", callback_data="text_gen:example")
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def text_generation_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="✅ Всё отлично, спасибо!", callback_data="text_result:ok"
        )
    )
    builder.add(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="text_result:edit")
    )
    builder.add(
        InlineKeyboardButton(
            text="🔄 Поменять картинку", callback_data="text_result:change_image"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def text_redactor_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="✅ Всё отлично, спасибо!", callback_data="text_editor:ok"
        )
    )
    builder.add(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="text_editor:edit")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def struct_form_start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="▶️ Начать", callback_data="struct_form:start")
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def struct_form_goal_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="📣 Результат", callback_data="struct_goal:result")
    )
    builder.add(
        InlineKeyboardButton(
            text="🙋 Волонтёры", callback_data="struct_goal:volunteers"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="💰 Пожертвования", callback_data="struct_goal:donations"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="✨ Работа организации", callback_data="struct_goal:work"
        )
    )
    builder.add(
        InlineKeyboardButton(text="❤️ Благодарность", callback_data="struct_goal:thanks")
    )
    builder.add(
        InlineKeyboardButton(text="📅 Анонс", callback_data="struct_goal:announcement")
    )
    builder.add(
        InlineKeyboardButton(text="✏️ Другое", callback_data="struct_goal:other")
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(2)
    return builder.as_markup()


def struct_form_platform_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="💬 Telegram", callback_data="struct_platform:telegram"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🖋️ ВКонтакте", callback_data="struct_platform:vk")
    )
    builder.add(
        InlineKeyboardButton(
            text="🌐 Универсально", callback_data="struct_platform:universal"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def struct_form_audience_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="👥 Местные жители", callback_data="struct_audience:locals"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🎓 Молодёжь", callback_data="struct_audience:youth")
    )
    builder.add(
        InlineKeyboardButton(text="💸 Доноры", callback_data="struct_audience:donors")
    )
    builder.add(
        InlineKeyboardButton(
            text="🤝 Волонтёры", callback_data="struct_audience:volunteers"
        )
    )
    builder.add(
        InlineKeyboardButton(text="📰 СМИ", callback_data="struct_audience:media")
    )
    builder.add(
        InlineKeyboardButton(
            text="🌍 Широкая аудитория", callback_data="struct_audience:broad"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(2)
    return builder.as_markup()


def struct_form_style_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="❤️ Тёплый", callback_data="struct_style:warm")
    )
    builder.add(
        InlineKeyboardButton(text="📊 С фактами", callback_data="struct_style:facts")
    )
    builder.add(
        InlineKeyboardButton(text="💬 Просто", callback_data="struct_style:simple")
    )
    builder.add(
        InlineKeyboardButton(text="🧭 Официально", callback_data="struct_style:formal")
    )
    builder.add(
        InlineKeyboardButton(
            text="🔥 Эмоционально", callback_data="struct_style:emotional"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(2)
    return builder.as_markup()


def struct_form_length_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="✂️ Коротко", callback_data="struct_length:short")
    )
    builder.add(
        InlineKeyboardButton(text="📄 Средне", callback_data="struct_length:medium")
    )
    builder.add(
        InlineKeyboardButton(text="📚 Подробно", callback_data="struct_length:long")
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def struct_form_skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="struct_skip:skip")
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def image_style_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="📸 Реалистичное фото", callback_data="image_style:realistic"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🎨 Иллюстрация/рисунок", callback_data="image_style:illustration"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📱 Минимализм", callback_data="image_style:minimalism"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🎭 Постер/афиша", callback_data="image_style:poster")
    )
    builder.add(
        InlineKeyboardButton(
            text="💼 Деловой стиль", callback_data="image_style:business"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def image_colors_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="🔴 Тёплые (красный, оранжевый, жёлтый)",
            callback_data="image_colors:warm",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🔵 Холодные (синий, голубой, зелёный)",
            callback_data="image_colors:cold",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🌈 Яркие и контрастные", callback_data="image_colors:bright"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="⚪ Нейтральные и пастельные", callback_data="image_colors:neutral"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="💡 На ваш выбор (система сама подберёт)",
            callback_data="image_colors:auto",
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def image_generation_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="✅ Всё отлично", callback_data="image_result:ok")
    )
    builder.add(
        InlineKeyboardButton(
            text="🔄 Перегенерировать", callback_data="image_result:regenerate"
        )
    )
    builder.add(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="image_result:edit")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def image_mode_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="✨ Создать новое", callback_data="image_mode:create")
    )
    builder.add(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="image_mode:edit")
    )
    builder.add(
        InlineKeyboardButton(text="📋 По примеру", callback_data="image_mode:example")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def overlay_mode_keyboard(include_auto: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="🖼 Без текста", callback_data="overlay_mode:none")
    )
    builder.add(
        InlineKeyboardButton(
            text="📝 Добавить свою фразу", callback_data="overlay_mode:custom"
        )
    )
    if include_auto:
        builder.add(
            InlineKeyboardButton(
                text="🤖 Сгенерировать автоматически", callback_data="overlay_mode:auto"
            )
        )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def overlay_position_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="⬆️ Вверху", callback_data="overlay_position:top")
    )
    builder.add(
        InlineKeyboardButton(
            text="↔️ По центру", callback_data="overlay_position:center"
        )
    )
    builder.add(
        InlineKeyboardButton(text="⬇️ Снизу", callback_data="overlay_position:bottom")
    )
    builder.add(
        InlineKeyboardButton(
            text="🔄 На выбор бота", callback_data="overlay_position:auto"
        )
    )

    builder.adjust(2)
    return builder.as_markup()


def overlay_background_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="⬛ Тёмный фон", callback_data="overlay_bg:dark")
    )
    builder.add(
        InlineKeyboardButton(text="⬜ Светлый фон", callback_data="overlay_bg:light")
    )
    builder.add(
        InlineKeyboardButton(
            text="🪟 Прозрачный", callback_data="overlay_bg:transparent"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔄 На выбор бота", callback_data="overlay_bg:auto")
    )

    builder.adjust(2)
    return builder.as_markup()


def overlay_font_keyboard(font_options: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for font in font_options:
        label = (
            font.capitalize() if font not in ("random", "default") else "🎲 Случайный"
        )
        callback_value = font if font != "default" else "random"
        builder.add(
            InlineKeyboardButton(
                text=label, callback_data=f"overlay_font:{callback_value}"
            )
        )

    builder.adjust(1)
    return builder.as_markup()


def from_example_generation_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="✅ Всё отлично, спасибо!", callback_data="example_result:ok"
        )
    )
    builder.add(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="example_result:edit")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def post_schedule_main_keyboard() -> InlineKeyboardMarkup:
    """
    Меню расписания поста, доступное из главного меню по кнопке
    «📆 Запланировать пост».
    """
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="⏰ Установить напоминание",
            callback_data="post_schedule:set_reminder",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📆 Автопубликация",
            callback_data="post_schedule:set_autopost",
        )
    )
    builder.add(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()
