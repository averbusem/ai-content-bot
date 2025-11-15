from aiogram.fsm.state import State, StatesGroup


class MainMenuStates(StatesGroup):
    main_menu = State()


class NKODataStates(StatesGroup):
    nko_menu = State()

