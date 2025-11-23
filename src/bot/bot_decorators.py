import logging
from functools import wraps
from aiogram import types
from aiogram.fsm.context import FSMContext
from src.services.rate_limiter import rate_limiter
from src.config import settings
from src.bot.keyboards import back_to_menu_keyboard

logger = logging.getLogger(__name__)


def check_user_limit():
    """
    Декоратор для проверки лимита операций пользователя

    Usage:
        @check_user_limit()
        async def my_handler(message: Message, state: FSMContext):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Извлекаем message и state из аргументов
            message = None
            state = None
            user_id = None
            callback_query = None

            for arg in args:
                if isinstance(arg, types.Message):
                    message = arg
                    user_id = arg.from_user.id
                elif isinstance(arg, types.CallbackQuery):
                    callback_query = arg
                    message = arg.message
                    user_id = arg.from_user.id
                elif isinstance(arg, FSMContext):
                    state = arg

            if not message and "message" in kwargs:
                message = kwargs["message"]
                user_id = message.from_user.id

            if not message and "callback_query" in kwargs:
                callback_query = kwargs["callback_query"]
                message = callback_query.message
                user_id = callback_query.from_user.id

            if not state and "state" in kwargs:
                state = kwargs["state"]

            if not message or not user_id:
                logger.error("Декоратор check_user_limit: не найден message/callback")
                return await func(*args, **kwargs)

            user_key = f"user:{user_id}:operations"

            # Получаем текущее количество запросов
            remaining = await rate_limiter.get_remaining_requests(
                key=user_key,
                max_requests=settings.USER_OPERATIONS_LIMIT,
                window_seconds=settings.USER_OPERATIONS_WINDOW,
            )

            if remaining <= 0:
                remaining_time = await get_remaining_time(
                    user_key, settings.USER_OPERATIONS_WINDOW
                )

                minutes_text = "минут" if remaining_time != 1 else "минуту"
                time_info = (
                    f"через {remaining_time} {minutes_text}"
                    if remaining_time > 0
                    else "скоро"
                )

                await message.edit_text(
                    f"⏱ Превышен лимит операций.\n\n"
                    f"Доступно: {settings.USER_OPERATIONS_LIMIT} операций в интервале.\n"
                    f"Попробуйте {time_info}.",
                    reply_markup=back_to_menu_keyboard(),
                )

                if state:
                    await state.clear()

                if callback_query:
                    await callback_query.answer()

                return None

            result = await func(*args, **kwargs)

            if state:
                state_data = await state.get_data()
                operation_success = state_data.get("_operation_success", False)

                if operation_success:
                    try:
                        await rate_limiter.track_operation(
                            key=user_key,
                            max_requests=settings.USER_OPERATIONS_LIMIT,
                            window_seconds=settings.USER_OPERATIONS_WINDOW,
                        )
                        await state.update_data(_operation_success=False)
                    except Exception as e:
                        logger.warning(
                            f"Не удалось записать операцию для user {user_id}: {e}"
                        )

            return result

        return wrapper

    return decorator


async def track_user_operation(user_id: int) -> None:
    """
    Записать успешную операцию пользователя

    Usage:
        try:
            result = await ai_manager.generate_text(...)
            await message.answer(result)
            await track_user_operation(user_id)
        except Exception:
            await message.answer("Ошибка")
    """
    try:
        await rate_limiter.track_operation(
            key=f"user:{user_id}:operations",
            max_requests=settings.USER_OPERATIONS_LIMIT,
            window_seconds=settings.USER_OPERATIONS_WINDOW,
        )
    except Exception as e:
        logger.warning(f"Не удалось записать операцию для user {user_id}: {e}")


async def get_remaining_time(key: str, window_seconds: int) -> int:
    """
    Получить оставшееся время до сброса лимита (в минутах)
    """
    import time

    if not rate_limiter.redis_client:
        await rate_limiter.initialize()

    rate_key = f"rate_limit:{key}"

    try:
        oldest = await rate_limiter.redis_client.zrange(rate_key, 0, 0, withscores=True)

        if not oldest:
            return 0

        oldest_timestamp = oldest[0][1]
        time_passed = time.time() - oldest_timestamp
        remaining = max(0, window_seconds - time_passed)

        return int(remaining / 60)
    except Exception as e:
        logger.error(f"Ошибка получения remaining_time: {e}")
        return 0
