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

