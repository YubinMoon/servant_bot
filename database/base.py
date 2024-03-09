import logging
from typing import TYPE_CHECKING

import redis

if TYPE_CHECKING:
    from bot import ServantBot


class DatabaseManager:
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot
        self.database: redis.Redis = bot.database
        self.logger: logging.Logger = bot.logger
