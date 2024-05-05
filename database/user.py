from sys import prefix
from typing import TYPE_CHECKING

from .base import DatabaseManager

if TYPE_CHECKING:
    from discord import User

    from bot import ServantBot


class UserDataManager(DatabaseManager):
    prefix = "user"

    def __init__(self, bot: "ServantBot", user: "User") -> None:
        super().__init__(bot)
        self.user = user

    def _get_id(self, keys: list[str]) -> str:
        return ":".join([self.prefix, self.user.global_name, *keys])

    def get_token(self) -> bytes | None:
        return self.database.get(self._get_id(["token", "balance"]))

    def set_token(self, balance: int) -> None:
        self.database.set(self._get_id(["token", "balance"]), balance)

    def get_used_tokens(self, model: str) -> dict[str, int]:
        return self.database.hgetall(self._get_id(["token", f"used-{model}"]))

    def set_used_tokens(self, model: str, data: dict[str, int]) -> None:
        self.database.hmset(self._get_id(["token", f"used-{model}"]), data)
