from aiogram import Router

from src.bot.handlers.start import router as router_start
from src.bot.handlers.menu import router as router_menu
from src.bot.handlers.nko_data import router as router_nko_data
from src.bot.handlers.help import router as router_help
from src.bot.handlers.text_generation import router as router_text_generation
from src.bot.handlers.text_generation_struct import router as router_text_generation_struct


router = Router()


def get_handlers_router() -> Router:
    router.include_router(router_start)
    router.include_router(router_menu)
    router.include_router(router_nko_data)
    router.include_router(router_help)
    router.include_router(router_text_generation)
    router.include_router(router_text_generation_struct)

    return router
