import json
from ast import Bytes
from typing import TYPE_CHECKING

from numpy import byte

from .base import DatabaseManager, get_redis

if TYPE_CHECKING:
    from bot import ServantBot


class ChatDataManager(DatabaseManager):
    def __init__(self, bot: "ServantBot") -> None:
        super().__init__(bot)

    def has_lock(self, guild_name: str, key: str) -> bool:
        num_of_keys = self.database.exists(f"chat:{guild_name}:{key}:lock")
        return num_of_keys > 0

    def lock(self, guild_name: str, key: str) -> None:
        self.database.set(f"chat:{guild_name}:{key}:lock", "1")

    def unlock(self, guild_name: str, key: str) -> None:
        self.database.delete(f"chat:{guild_name}:{key}:lock")

    def get_system_message(self, guild_name: str, key: str) -> str | None:
        raw_text = self.database.get(f"chat:{guild_name}:{key}:system")
        if raw_text is None:
            return None
        return raw_text.decode("utf-8")

    def set_system_message(self, guild_name: str, key: str, message: str) -> None:
        self.database.set(f"chat:{guild_name}:{key}:system", message)

    def get_messages(self, guild_name: str, key: str) -> list[dict]:
        data = self.database.json().get(f"chat:{guild_name}:{key}:messages", "$")
        self.database.json().arrpop
        if data is None:
            return []
        return data[0]

    def trim_messages(self, guild_name: str, key: str, max_length: int) -> None:
        self.database.json().arrtrim(
            f"chat:{guild_name}:{key}:messages", "$", 0, max_length
        )

    def append_message(self, guild_name: str, key: str, message: dict) -> None:
        self.database.json().set(f"chat:{guild_name}:{key}:messages", "$", [], nx=True)
        self.database.json().arrappend(
            f"chat:{guild_name}:{key}:messages", "$", message
        )

    def memory_exists(self, key: str) -> bool:
        num_of_keys = self.database.keys(f"{key}")
        return len(num_of_keys) > 0

    def set_redis_schema(self, prefix_key: str, schema: dict) -> None:
        self.database.set(f"{prefix_key}:schema", json.dumps(schema))

    def get_redis_schema(self, prefix_key: str) -> dict | None:
        result = self.database.get(f"{prefix_key}:schema")
        if result is None:
            return None
        return json.loads(result)


async def set_thread_info(guild_name: str, key: str, data: dict) -> None:
    db = await get_redis()
    db.json().set(f"chat:{guild_name}:{key}:info", "$", data)


async def get_thread_info(guild_name: str, key: str) -> dict | None:
    db = await get_redis()
    result = db.json().get(f"chat:{guild_name}:{key}:info")
    if result is None:
        return None
    return result


async def has_lock(guild_name: str, key: str) -> bool:
    db = await get_redis()
    num_of_keys = db.exists(f"chat:{guild_name}:{key}:lock")
    return num_of_keys > 0


async def lock(guild_name: str, key: str) -> None:
    db = await get_redis()
    db.set(f"chat:{guild_name}:{key}:lock", "1")


async def unlock(guild_name: str, key: str) -> None:
    db = await get_redis()
    db.delete(f"chat:{guild_name}:{key}:lock")
