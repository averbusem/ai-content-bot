import asyncio
import logging

from src.bot import bot, dp, setup_bot
from src.db.database import engine
from src.jobs.scheduler import init_scheduler
from src.utils.setup_certificates import setup_certificates


async def main():
    setup_certificates()

    # Инициализируем планировщик задач APScheduler
    scheduler = init_scheduler(engine)

    await setup_bot()

    # Запускаем APScheduler после инициализации бота
    scheduler.start()

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Останавливаем планировщик при завершении работы приложения
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
