import discord

from .base import DatabaseManager


class ChatDataManager(DatabaseManager):
    def __init__(self, bot):
        super().__init__(bot)

    def set_thread(self, thread_id: int) -> None:
        obj = {
            "messages": [],
            "system": "",
        }
        self.database.json().set(f"chat:{thread_id}", "$", obj)

    def get_thread(self, thread_id: int) -> dict | None:
        return self.database.json().get(f"chat:{thread_id}", "$")[0]

    def thread_exists(self, thread_id: int) -> bool:
        return self.database.exists(f"chat:{thread_id}")

    def append_message(self, thread_id: int, message: dict) -> None:
        self.database.json().arrappend(f"chat:{thread_id}", "$.messages", message)
