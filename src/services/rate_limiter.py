import redis.asyncio as redis
from typing import Optional
import time
from src.config import settings


class RateLimitError(Exception):
    """Исключение при превышении rate limit"""

    pass


class RateLimiter:
    """Rate limiter на основе Redis"""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client: Optional[redis.Redis] = None
        self.redis_url = redis_url or "redis://localhost:6379"

    async def initialize(self):
        """Инициализация подключения к Redis"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                self.redis_url, decode_responses=True
            )

    async def close(self):
        """Закрытие подключения к Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> bool:
        """
        Проверка rate limit для ключа

        Args:
            key: Уникальный ключ (например, "gigachat:api" или "user:123")
            max_requests: Максимальное количество запросов
            window_seconds: Временное окно в секундах

        Returns:
            True если запрос можно выполнить, False если достигнут лимит
        """
        if not self.redis_client:
            await self.initialize()

        current_time = time.time()
        window_start = current_time - window_seconds

        # Ключ для хранения списка запросов
        rate_key = f"rate_limit:{key}"

        await self.redis_client.zremrangebyscore(rate_key, 0, window_start)
        request_count = await self.redis_client.zcard(rate_key)

        if request_count >= max_requests:
            return False

        await self.redis_client.zadd(rate_key, {str(current_time): current_time})
        await self.redis_client.expire(rate_key, window_seconds)

        return True

    async def get_remaining_requests(
        self, key: str, max_requests: int, window_seconds: int
    ) -> int:
        """
        Получить количество оставшихся запросов

        Returns:
            Количество доступных запросов
        """
        if not self.redis_client:
            await self.initialize()

        current_time = time.time()
        window_start = current_time - window_seconds

        rate_key = f"rate_limit:{key}"

        await self.redis_client.zremrangebyscore(rate_key, 0, window_start)
        request_count = await self.redis_client.zcard(rate_key)

        return max(0, max_requests - request_count)

    async def track_operation(self, key: str, max_requests: int, window_seconds: int):
        """
        Отслеживание операции (вызывается вручную в handlers)
        """
        can_proceed = await self.check_rate_limit(key, max_requests, window_seconds)
        if not can_proceed:
            raise RateLimitError(
                f"Превышен лимит: {max_requests} операций в течение {window_seconds // 60} минут"
            )


rate_limiter = RateLimiter(redis_url=settings.REDIS_URL)
