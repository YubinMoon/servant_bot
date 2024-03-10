import random
from typing import TYPE_CHECKING

from discord import Embed

from utils import color

from .base import BaseHandler
from .error import MemberNumError

if TYPE_CHECKING:
    from discord import Member
    from discord.ext.commands import Context

    from bot import ServantBot


class ShuffleTeamHandler(BaseHandler):
    logger_name = "shuffle_team_handler"
    LANE = ["탑", "정글", "미드", "원딜", "서폿"]

    def __init__(self, bot: "ServantBot", context: "Context", team_name: str) -> None:
        super().__init__(bot, context, team_name)
        self.base_weight = [[10000.0 for _ in range(5)] for _ in range(5)]
        self.multiple = 0.1

    async def action(self):
        members_id = await self.db.get_members(self.guild.name, self.team_name)
        members = [self.guild.get_member(member) for member in members_id]
        if len(members) not in [5, 10]:
            raise MemberNumError(
                f"Team {self.team_name} has {len(members)} members. It should be 5 or 10.",
                self.team_name,
            )
        if len(members) == 5:
            await self.shuffle_rank(members)
        elif len(members) == 10:
            await self.shuffle_custom(members)

    async def shuffle_rank(self, members: "list[Member]") -> None:
        team = await self.get_rank_team()
        await self.db.add_history(self.guild.name, self.team_name, team)
        embed = Embed(
            title=f"{self.team_name} 팀",
            description="라인을 배정했어요.",
            color=color.BASE,
        )
        for l, m in enumerate(team):
            member = members[m]
            embed.add_field(
                name=self.LANE[l],
                value=f"{member.mention} ({member.global_name or member.name})",
                inline=False,
            )
        await self.context.send(embed=embed)

    async def get_rank_team(self) -> list[int]:
        team = []
        weights = await self.get_weight()
        while len(set(team)) != 5:
            team.clear()
            for i in range(5):
                team.append(random.choices(range(5), weights=weights[i])[0])
        new_team = team.copy()
        for i, member in enumerate(team):
            new_team[member] = i
        return new_team

    async def get_weight(self) -> list[list[float]]:
        weight = self.base_weight.copy()
        records = await self.db.get_history(self.guild.name, self.team_name)
        for record in records:
            weight = self.calc_weight(weight, record)
        return weight

    def calc_weight(
        self, weight: list[list[float]], record: list[int]
    ) -> list[list[float]]:
        new_weight = weight.copy()
        for lane_no, member_no in enumerate(record):
            remain = (new_weight[member_no][lane_no] * (1 - self.multiple)) // 4
            for i in range(5):
                if i == lane_no:
                    new_weight[member_no][i] -= remain * 4
                else:
                    new_weight[member_no][i] += remain
        return new_weight

    async def shuffle_custom(self, members: "list[Member]") -> None:
        random.shuffle(members)
        embed = Embed(
            title=f"{self.team_name} 팀",
            description="새로운 대전을 구성했어요.",
            color=0xBEBEFE,
        )
        embed.add_field(
            name="1팀",
            value="\n".join(
                [
                    f"{member.mention} ({member.global_name or member.name})"
                    for member in members[:5]
                ]
            ),
            inline=False,
        )
        embed.add_field(
            name="2팀",
            value="\n".join(
                [
                    f"{member.mention} ({member.global_name or member.name})"
                    for member in members[5:]
                ]
            ),
            inline=False,
        )
        await self.context.send(embed=embed)
