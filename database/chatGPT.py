from typing import TYPE_CHECKING

from .base import DatabaseManager

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
        return self.database.json().get(f"chat:{guild_name}:{key}:messages", "$")[0]

    def append_message(self, guild_name: str, key: str, message: dict) -> None:
        self.database.json().set(f"chat:{guild_name}:{key}:messages", "$", [], nx=True)
        self.database.json().arrappend(
            f"chat:{guild_name}:{key}:messages", "$", message
        )
