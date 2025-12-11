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
            text="⏳ Запланировать пост", callback_data="main_menu:schedule_post"
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    return builder.as_markup()


def help_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    sections = [
        ("📝 Создание поста", "help:section:posts"),
        ("🎨 Создание картинки", "help:section:images"),
        ("✏️ Редактор текста", "help:section:text_editor"),
        ("📅 Контент-план", "help:section:content_plan"),
        ("⏰ Запланировать пост", "help:section:schedule"),
        ("⚙️ Информация о НКО", "help:section:nko"),
        ("💡 Советы", "help:section:tips"),
    ]

    for text, callback_data in sections:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))

    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def help_section_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="⬅️ Разделы помощи", callback_data="help:menu")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def nko_data_empty_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="📝 Заполнить данные", callback_data="nko_menu:fill_data"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    return builder.as_markup()


def nko_skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="nko_skip:skip")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def text_generation_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✏️ Изменить текст", callback_data="text_result:edit")
    )
    builder.add(
        InlineKeyboardButton(
            text="📎 Добавить фото/логотип", callback_data="text_result:add_overlay"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🔄 Поменять картинку", callback_data="text_result:change_image"
        )
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def text_redactor_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="text_editor:edit")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def struct_form_start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="▶️ Начать", callback_data="struct_form:start")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def struct_form_skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="struct_skip:skip")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def image_generation_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="🔄 Перегенерировать", callback_data="image_result:regenerate"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📎 Добавить фото/логотип", callback_data="image_result:add_overlay"
        )
    )
    builder.add(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="image_result:edit")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
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


def image_attachment_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="🏷 Логотип / стикер", callback_data="image_asset:type:logo"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🖼 Фото / иллюстрация", callback_data="image_asset:type:photo"
        )
    )
    builder.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data="image_asset:type:cancel")
    )

    builder.adjust(1)
    return builder.as_markup()


def image_attachment_position_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="↖️ Верхний левый", callback_data="image_asset:pos:top_left"
        ),
        InlineKeyboardButton(
            text="↗️ Верхний правый", callback_data="image_asset:pos:top_right"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="↙️ Нижний левый", callback_data="image_asset:pos:bottom_left"
        ),
        InlineKeyboardButton(
            text="↘️ Нижний правый", callback_data="image_asset:pos:bottom_right"
        ),
    )
    builder.add(
        InlineKeyboardButton(text="⏺ По центру", callback_data="image_asset:pos:center")
    )
    builder.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data="image_asset:pos:cancel")
    )

    builder.adjust(2, 1, 1)
    return builder.as_markup()


def from_example_generation_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="example_result:edit")
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def post_schedule_confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения настроек запланированного поста.
    """
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="✅ Подтвердить", callback_data="post_schedule:confirm"
        )
    )
    builder.add(
        InlineKeyboardButton(text="❌ Отменить", callback_data="post_schedule:cancel")
    )

    builder.adjust(1)
    return builder.as_markup()


def post_schedule_remind_offset_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора интервала напоминания перед публикацией.
    """
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="15 минут",
            callback_data="post_schedule:remind_offset:15",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="30 минут",
            callback_data="post_schedule:remind_offset:30",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="1 час",
            callback_data="post_schedule:remind_offset:60",
        )
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def content_plan_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подменю контент-плана."""
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="➕ Создать контент план",
            callback_data="content_plan:create",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="📋 Посмотреть контент планы",
            callback_data="content_plan:list",
        )
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def content_plans_list_keyboard(
    plans: list, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    """Клавиатура со списком контент-планов и пагинацией."""
    builder = InlineKeyboardBuilder()

    for plan in plans:
        plan_date = plan.created_at.strftime("%d.%m.%Y")
        text = f"{plan.name} - {plan_date}"
        if len(text) > 50:
            text = text[:47] + "..."
        builder.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f"content_plan:view:{plan.id}",
            )
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"content_plan:list_page:{page - 1}",
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ▶️",
                callback_data=f"content_plan:list_page:{page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def content_plan_days_keyboard(
    days: list, plan_id: int, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    """Клавиатура с днями контент-плана и пагинацией."""
    builder = InlineKeyboardBuilder()

    for day in days:
        day_text = f"{day.day_name} {day.date}, {day.time}"
        if day.topic:
            topic_short = day.topic[:30] + "..." if len(day.topic) > 30 else day.topic
            day_text = f"{day_text}\n{topic_short}"
        if len(day_text) > 50:
            day_text = day_text[:47] + "..."
        builder.add(
            InlineKeyboardButton(
                text=day_text,
                callback_data=f"content_plan:day:{day.id}",
            )
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"content_plan:days_page:{plan_id}:{page - 1}",
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперёд ▶️",
                callback_data=f"content_plan:days_page:{plan_id}:{page + 1}",
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.add(
        InlineKeyboardButton(
            text="🗑 Удалить этот контент-план",
            callback_data=f"content_plan:delete:{plan_id}",
        )
    )

    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()


def content_plan_day_detail_keyboard(day_id: int, plan_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра дня контент-плана."""
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="📝 Сгенерировать пост",
            callback_data=f"content_plan:generate_post:{day_id}",
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="⬅️ К дням плана",
            callback_data=f"content_plan:view:{plan_id}",
        )
    )
    builder.add(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu:back")
    )

    builder.adjust(1)
    return builder.as_markup()
