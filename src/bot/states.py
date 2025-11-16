from aiogram.fsm.state import State, StatesGroup


class MainMenuStates(StatesGroup):
    main_menu = State()


class NKODataStates(StatesGroup):
    nko_menu = State()
    name = State()
    activity = State()
    forms = State()
    forms_other = State()
    region = State()
    contacts = State()


class TextGenerationStates(StatesGroup):
    method_selection = State()
    free_text_input = State()
    waiting_results = State()
    editing = State()


class TextGenerationStructStates(StatesGroup):
    method_selection = State()
    start = State()
    question_1_event = State()  # О каком событии пост?
    question_2_description = State()  # Описание события подробнее
    question_3_goal = State()  # Главная цель поста
    question_3_goal_other = State()  # Если выбрано "Другое" в цели
    question_4_date = State()  # Дата и время
    question_5_location = State()  # Место проведения
    question_6_platform = State()  # Площадка публикации
    question_7_audience = State()  # Целевая аудитория
    question_8_style = State()  # Стиль текста
    question_9_length = State()  # Объём текста
    question_10_additional = State()  # Дополнительная информация
    waiting_results = State()
    editing = State()


class TextEditorStates(StatesGroup):
    post_input = State()
    edit_input = State()
    waiting_results = State()
    editing = State()


class ImageGenerationStates(StatesGroup):
    mode_selection = State()           # Выбор режима
    description = State()              # Описание
    style = State()                    # Стиль
    colors = State()                   # Цвета
    upload_for_edit = State()          # Загрузка для редактирования
    edit_prompt = State()              # Промпт редактирования
    upload_example = State()           # Загрузка примера
    example_prompt = State()           # Промпт по примеру
    waiting_results = State()


class ContentPlanStates(StatesGroup):
    duration_input = State()
    frequency_input = State()
    preferences_input = State()
    waiting_results = State()