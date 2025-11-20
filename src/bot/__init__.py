from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage


from aiogram.types import BotCommand

from src.bot.handlers import get_handlers_router
from src.bot.middlewares import RemoveLastKeyboardMiddleware
from src.config import settings

bot = Bot(
    token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = RedisStorage.from_url(settings.REDIS_URL)
dp = Dispatcher(storage=storage)

dp.message.middleware(RemoveLastKeyboardMiddleware())
dp.callback_query.middleware(RemoveLastKeyboardMiddleware())

dp.include_router(get_handlers_router())


async def setup_bot():
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Перезапустить бота"),
        ]
    )
    await bot.delete_webhook(drop_pending_updates=True)
