import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Optional

import redis

if TYPE_CHECKING:
    from bot import ServantBot

_redis: Optional[redis.Redis] = None


@asynccontextmanager
async def get_redis():
    global _redis
    if _redis is None:
        _redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )
        failed_time = 0
        while True:
            if failed_time > 3:
                raise Exception("Failed to connect to the Redis server")
            try:
                _redis.ping()
                break
            except Exception as e:
                failed_time += 1
                await asyncio.sleep(1)

    try:
        yield _redis
    finally:
        pass
