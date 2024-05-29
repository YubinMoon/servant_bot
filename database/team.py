import json
from typing import TYPE_CHECKING

from utils.logger import get_logger

from .base import DatabaseManager, get_redis

if TYPE_CHECKING:
    from discord import Guild, Member, User


class TeamDataManager(DatabaseManager):
    def __init__(self, guild: "Guild", team_name: str) -> None:
        self.guild = guild
        self.team_name = team_name

        self.key_prefix = "team"
        self.key_guild = f"{self.key_prefix}:{guild.name}"
        self.key_team = f"{self.key_guild}:{team_name}"

        self.logger = get_logger("team_data_manager")

    async def new_team(self, message_id: int) -> None:
        db = await get_redis()
        guild_name = self.guild.name
        await self._delete_previous_team()
        db.set(f"{self.key_team}:message", message_id)
        db.set(f"{self.key_guild}:last", self.team_name)

    async def _delete_previous_team(self) -> None:
        db = await get_redis()
        keys: list[str] = db.keys(f"{self.key_team}:*")
        if keys:
            self.logger.warning(f"overwrite team: {self.team_name}")
            for key in keys:
                db.delete(key)
                self.logger.debug(f"Deleted key: {key}")

    async def get_team_name(self) -> str | None:
        db = await get_redis()
        value: str | None = db.get(f"{self.key_guild}:last")
        return value

    async def get_message_id(self) -> int | None:
        db = await get_redis()
        value: str | None = db.get(f"{self.key_team}:message")
        self.logger.info(msg=f"{self.key_team}:message")
        if value is None:
            return None
        return int(value)

    async def get_members(self) -> list[int]:
        db = await get_redis()
        members: list[str] = db.lrange(f"{self.key_team}:members", 0, -1)
        return [json.loads(member)["id"] for member in members]

    async def add_member(self, member: "Member | User") -> None:
        db = await get_redis()
        member_data = json.dumps({"id": member.id, "name": member.name})
        db.rpush(f"{self.key_team}:members", member_data)

    async def pop_member(self, index: int) -> None:
        db = await get_redis()
        member_data: list[bytes] = db.lrange(f"{self.key_team}:members", 0, -1)
        member_data.pop(index)
        db.delete(f"{self.key_team}:members")
        for member in member_data:
            db.rpush(f"{self.key_team}:members", member)

    async def add_history(self, team: list[int]) -> None:
        db = await get_redis()
        history = json.dumps(team)
        db.rpush(f"{self.key_team}:history", history)

    async def get_history(self) -> list[list[int]]:
        db = await get_redis()
        histories: list[bytes] = db.lrange(f"{self.key_team}:history", 0, -1)
        return [json.loads(history) for history in histories]
