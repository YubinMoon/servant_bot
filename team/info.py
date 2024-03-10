from typing import TYPE_CHECKING

from discord import Embed

from utils import color

from .base import BaseHandler
from .error import NoMemberError

if TYPE_CHECKING:
    from discord import Member
    from discord.ext.commands import Context

    from bot import ServantBot


class TeamInfoHandler(BaseHandler):
    logger_name = "team_info_handler"

    def __init__(
        self, bot: "ServantBot", context: "Context", team_name: str = ""
    ) -> None:
        super().__init__(bot, context, team_name)

    async def action(self):
        members = await self.get_members()
        await self.send_result(members)

    async def get_members(self):
        members_id = await self.db.get_members(self.guild.name, self.team_name)
        members = [self.guild.get_member(member) for member in members_id]
        members = [member for member in members if member is not None]
        if members == []:
            raise NoMemberError(f"No member in {self.team_name} team.", self.team_name)
        return members

    async def send_result(self, members: "list[Member]"):
        embed = Embed(
            title=f"**{self.team_name}** 팀",
            color=color.BASE,
        )
        embed.add_field(
            name=f"현재 팀원: {len(members)}",
            value="\n".join(
                [f"{member.mention} ({member.name})" for member in members]
            ),
        )
        await self.context.send(embed=embed, ephemeral=True, silent=True)
