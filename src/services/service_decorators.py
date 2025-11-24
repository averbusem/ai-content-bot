import asyncio
import logging
from functools import wraps
from typing import Callable
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
