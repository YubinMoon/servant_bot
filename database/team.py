import discord

from .base import DatabaseManager


class TeamDataManager(DatabaseManager):
    def __init__(self, bot):
        super().__init__(bot)
        self.base_weight = [[10000 for _ in range(5)] for _ in range(5)]

    async def start_team(self, channel_id: int, message_id: int) -> None:
        obj = {
            "message_id": message_id,
            "weights": self.base_weight.copy(),
            "members": [],
            "history": [],
        }
        self.database.json().set(f"team:{channel_id}", "$", obj, decode_keys=True)

    async def get_team(self, channel_id: int) -> dict | None:
        return self.database.json().get(f"team:{channel_id}", "$")

    async def get_members(self, channel_id: int) -> list[discord.Member]:
        members_id = self.database.json().get(f"team:{channel_id}", "$.members")[0]
        channel = self.bot.get_channel(channel_id)
        members = [channel.guild.get_member(member) for member in members_id]
        return members

    async def get_message(self, channel_id: int) -> discord.Message:
        message_id = self.database.json().get(f"team:{channel_id}", "$.message_id")[0]
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        return message

    async def is_member_in_team(self, channel_id: int, member: discord.Member) -> bool:
        member_list = self.database.json().get(f"team:{channel_id}", "$.members")
        return member.name in member_list

    async def get_member_num(self, channel_id: int) -> int:
        return self.database.json().arrlen(f"team:{channel_id}", "$.members")[0]

    async def add_member(self, channel_id: int, member: discord.Member) -> None:
        self.database.json().arrappend(f"team:{channel_id}", "$.members", member.id)

    async def pop_member(self, channel_id: int, member: discord.Member) -> None:
        members = self.database.json().get(f"team:{channel_id}", "$.members")[0]
        index = members.index(member.id)
        self.database.json().arrpop(f"team:{channel_id}", "$.members", index)

    def get_weights(self, channel_id: int) -> list[list[int]]:
        return self.database.json().get(f"team:{channel_id}", "$.weights")[0]

    def set_weights(self, channel_id: int, weights: list[list[int]]) -> None:
        self.database.json().set(f"team:{channel_id}", "$.weights", weights)
