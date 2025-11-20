import json
from typing import Optional, Dict, Any

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from src.config import settings


class NKOService:
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.redis: Optional[Redis] = None

    async def _get_redis(self) -> Redis:
        if self.redis is None:
            self.pool = ConnectionPool.from_url(settings.REDIS_URL)
            self.redis = Redis(connection_pool=self.pool)
        return self.redis

    async def get_nko_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        redis = await self._get_redis()
        key = f"nko_data:{user_id}"
        data = await redis.get(key)
        if data:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return json.loads(data)
        return None

    async def save_nko_data(self, user_id: int, data: Dict[str, Any]) -> None:
        redis = await self._get_redis()
        key = f"nko_data:{user_id}"
        await redis.set(key, json.dumps(data, ensure_ascii=False))

    async def delete_nko_data(self, user_id: int) -> None:
        redis = await self._get_redis()
        key = f"nko_data:{user_id}"
        await redis.delete(key)

    async def close(self):
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()


nko_service = NKOService()
