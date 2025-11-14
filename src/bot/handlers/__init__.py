from aiogram import Router

from src.bot.handlers.start import router as router_start


router = Router()


def get_handlers_router() -> Router:
    router.include_router(router_start)

    return router
