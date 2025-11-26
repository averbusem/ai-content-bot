import asyncio
import logging
from functools import wraps
from typing import Callable, Awaitable
import httpx
from src.config import settings

logger = logging.getLogger(__name__)


def with_retry(func: Callable):
    """
    Декоратор для retry

    Usage:
        @with_retry
        async def my_api_call():
            ...
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        last_exception = None

        for attempt in range(settings.MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < settings.MAX_RETRIES - 1:
                    wait_time = min(
                        settings.RETRY_MIN_WAIT * (2**attempt), settings.RETRY_MAX_WAIT
                    )
                    logger.warning(
                        f"Retry {attempt + 1}/{settings.MAX_RETRIES} "
                        f"after {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All retries failed: {str(e)}")

        raise last_exception

    return wrapper


class TextLengthLimitError(Exception):
    """Raised when we fail to produce text within configured limits."""


def ensure_text_length(
    max_length: int = 1024,
    max_attempts: int = 3,
) -> Callable[[Callable[..., Awaitable[str]]], Callable[..., Awaitable[str]]]:
    """
    Декоратор для повторной генерации текста, если его длина больше `max_length`
    """

    def decorator(func: Callable[..., Awaitable[str]]):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> str:
            for attempt in range(max_attempts):
                text = await func(*args, **kwargs)
                sanitized = (text or "").strip()
                if not sanitized or len(sanitized) <= max_length:
                    return sanitized

                logger.warning(
                    "Generated text exceeded %s chars on attempt %s/%s",
                    max_length,
                    attempt + 1,
                    max_attempts,
                )

            raise TextLengthLimitError(
                f"Max length {max_length} exceeded after {max_attempts} attempts"
            )

        return wrapper

    return decorator
