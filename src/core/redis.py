"""Redis client configuration."""

import redis.asyncio as redis
from redis.asyncio import Redis

from src.config import settings
from src.shared.logger import logger

_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """Get Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info(f"Redis connected | url={settings.REDIS_URL}")
    
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


async def check_redis_connection() -> bool:
    """Check Redis connection."""
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection failed | error={e}")
        return False


class RedisCache:
    """Helper class for Redis caching operations."""

    def __init__(self, prefix: str = "cache"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> str | None:
        """Get value from cache."""
        client = await get_redis()
        return await client.get(self._key(key))

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Set value in cache."""
        client = await get_redis()
        await client.set(self._key(key), value, ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        client = await get_redis()
        await client.delete(self._key(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await get_redis()
        return bool(await client.exists(self._key(key)))

    async def get_json(self, key: str) -> dict | list | None:
        """Get JSON value from cache."""
        import json
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(self, key: str, value: dict | list, ttl: int | None = None) -> None:
        """Set JSON value in cache."""
        import json
        await self.set(key, json.dumps(value, ensure_ascii=False), ttl)


# Cache instances for different purposes
user_cache = RedisCache(prefix="user")
models_cache = RedisCache(prefix="models")
generation_cache = RedisCache(prefix="generation")
