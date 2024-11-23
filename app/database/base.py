import os
from contextlib import asynccontextmanager, contextmanager
from logging import getLogger
from typing import TYPE_CHECKING, Optional

import redis
from redis.asyncio import Redis as AsyncRedis

logger = getLogger(__name__)

_aredis: Optional[AsyncRedis] = None
_redis: Optional[redis.Redis] = None


@asynccontextmanager
async def get_async_redis():
    global _aredis
    try:
        if _aredis is None:
            _aredis = AsyncRedis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True,
            )
        yield _aredis
    except redis.ConnectionError as e:
        logger.error(f"Async connection error: {e}")
        raise


@contextmanager
def get_sync_redis():
    global _redis
    try:
        if _redis is None:
            _redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True,
            )
        yield _redis
    except redis.ConnectionError as e:
        logger.error(f"Async connection error: {e}")
        raise
