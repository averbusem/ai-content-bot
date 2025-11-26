import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage


from aiogram.types import BotCommand

from src.bot.handlers import get_handlers_router
from src.bot.middlewares import (
    DBSessionMiddleware,
    RemoveLastKeyboardMiddleware,
    UserAccessMiddleware,
    GroupChatAccessMiddleware,

)
from src.config import settings
from src.services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


bot = Bot(
    token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = RedisStorage.from_url(settings.REDIS_URL)
dp = Dispatcher(storage=storage)


db_session_middleware = DBSessionMiddleware()
dp.message.middleware(db_session_middleware)
dp.callback_query.middleware(db_session_middleware)

user_access_middleware = UserAccessMiddleware(bot=bot, admin_id=settings.ADMIN_ID)
dp.message.middleware(user_access_middleware)
dp.callback_query.middleware(user_access_middleware)

remove_keyboard_middleware = RemoveLastKeyboardMiddleware()
dp.message.middleware(remove_keyboard_middleware)
dp.callback_query.middleware(remove_keyboard_middleware)

dp.message.middleware(GroupChatAccessMiddleware(storage=storage))
dp.callback_query.middleware(GroupChatAccessMiddleware(storage=storage))



dp.include_router(get_handlers_router())


async def on_startup():
    try:
        await rate_limiter.initialize()
        logger.info("Redis подключен успешно")
    except Exception as e:
        logger.error(f"Ошибка подключения к Redis: {e}")
        raise


async def on_shutdown():
    try:
        await rate_limiter.close()
        logger.info("Redis отключен")
    except Exception as e:
        logger.error(f"Ошибка отключения Redis: {e}")


async def setup_bot():
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Перезапустить бота"),
            BotCommand(command="use", description="Стать инициатором в групповом чате"),
        ]
    )
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
