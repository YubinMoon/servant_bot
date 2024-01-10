import redis
import logging


class DatabaseManager:
    def __init__(self, *, r: redis.Redis, logger: logging.Logger) -> None:
        self.r = r
        self.logger = logger
        self.r.set("test", "test")
        self.logger.warn(self.r.get("test"))
