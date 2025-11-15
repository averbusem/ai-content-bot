from aiogram import Router

from src.bot.handlers.start import router as router_start
from src.bot.handlers.menu import router as router_menu
from src.bot.handlers.nko_data import router as router_nko_data


router = Router()


def get_handlers_router() -> Router:
    router.include_router(router_start)
    router.include_router(router_menu)
    router.include_router(router_nko_data)

    return router
