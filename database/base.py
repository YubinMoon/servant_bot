import asyncio
import logging
import os
from typing import TYPE_CHECKING

import redis

if TYPE_CHECKING:
    from bot import ServantBot


class DatabaseManager:
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot
        self.database: redis.Redis = bot.database
        self.logger: logging.Logger = bot.logger


async def get_redis():
    db = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
    )
    failed_time = 0
    while True:
        if failed_time > 3:
            raise Exception("Failed to connect to the Redis server")
        try:
            db.ping()
            break
        except:
            failed_time += 1
            await asyncio.sleep(1)
    return db
