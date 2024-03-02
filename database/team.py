import json

import discord

from bot import ServantBot
from utils.logger import get_logger

from .base import DatabaseManager


class TeamDataManager(DatabaseManager):
    def __init__(self, bot: ServantBot):
        super().__init__(bot)
        self.logger = get_logger("team_data_manager")

    async def start_team(
        self, guild_name: str, message_id: int, team_name: str
    ) -> None:
        # delete previous team data
        keys: list[bytes] = self.database.keys(f"team:{guild_name}:{team_name}:*")
        for key in keys:
            self.database.delete(key.decode("utf-8"))
            self.logger.debug(f"Deleted key: {key.decode('utf-8')}")
        self.database.set(f"team:{guild_name}:{team_name}:message", message_id)
        self.database.set(f"team:{guild_name}:last", team_name)

    async def get_team_name(self, guild_name: str) -> str:
        value: bytes = self.database.get(f"team:{guild_name}:last")
        if value is None:
            return ""
        return value.decode("utf-8")

    async def get_message_id(self, guild_name: str, team_name: str) -> int | None:
        value: bytes = self.database.get(f"team:{guild_name}:{team_name}:message")
        if value is None:
            return None
        return int(value.decode("utf-8"))

    async def get_members(self, guild_name: str, team_name: str) -> list[int]:
        members_b: list[bytes] = self.database.lrange(
            f"team:{guild_name}:{team_name}:members", 0, -1
        )
        if not members_b:
            return []
        return [json.loads(member.decode("utf-8"))["id"] for member in members_b]

    async def add_member(
        self, guild_name: str, team_name: str, member: discord.Member|discord.User
    ) -> None:
        member_data = json.dumps({"id": member.id, "name": member.name})
        self.database.rpush(f"team:{guild_name}:{team_name}:members", member_data)

    async def pop_member(self, guild_name: str, team_name: str, index: int) -> None:
        member_data: list[bytes] = self.database.lrange(
            f"team:{guild_name}:{team_name}:members", 0, -1
        )
        member_data.pop(index)
        self.database.delete(f"team:{guild_name}:{team_name}:members")
        for member in member_data:
            self.database.rpush(f"team:{guild_name}:{team_name}:members", member)

    async def add_history(
        self, guild_name: str, team_name: str, team: list[int]
    ) -> None:
        history = json.dumps(team)
        self.database.rpush(f"team:{guild_name}:{team_name}:history", history)

    async def get_history(self, guild_name: str, team_name: str) -> list[list[int]]:
        history_b: list[bytes] = self.database.lrange(
            f"team:{guild_name}:{team_name}:history", 0, -1
        )
        if not history_b:
            return []
        return [json.loads(history.decode("utf-8")) for history in history_b]
