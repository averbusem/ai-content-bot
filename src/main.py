import asyncio
import logging

from src.bot import bot, dp, setup_bot


async def main():
    await setup_bot()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
