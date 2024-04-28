from typing import TYPE_CHECKING

import discord

from .error import RankMemberNumError
from .shuffle import ShuffleTeamHandler

if TYPE_CHECKING:
    from discord import Member
    from discord.ext.commands import Context

    from bot import ServantBot


class TeamPredictHandler(ShuffleTeamHandler):
    logger_name = "team_predict_handler"

    def __init__(self, bot: "ServantBot", context: "Context", team_name: str) -> None:
        super().__init__(bot, context, team_name)

    async def action(self):
        members_id = await self.db.get_members(self.guild.name, self.team_name)
        members = [self.guild.get_member(member) for member in members_id]
        if len(members) == 5:
            await self.predict(members)
        else:
            raise RankMemberNumError(
                f"Team {self.team_name} has {len(members_id)} members. It should be 5.",
                self.team_name,
            )

    async def predict(self, members: "list[Member]") -> None:
        weight = await self.get_weight()
        embed = discord.Embed(
            title=f"{self.team_name} 팀 라인 예측",
            color=0xBEBEFE,
        )
        for i, m in enumerate(weight):
            member = members[i]
            weight_sum = sum(m)
            percent = [int(w / weight_sum * 100) for w in m]
            data = [f"`{l}`: **{p}**%" for l, p in zip(self.LANE, percent)]
            embed.add_field(
                name=f"**{member.display_name}** ({member.global_name or member.name})",
                value=" - ".join(data),
                inline=False,
            )
        await self.context.send(embed=embed, ephemeral=True, silent=True)
