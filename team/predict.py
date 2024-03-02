from typing import TYPE_CHECKING

import discord

from .base import BaseHandler

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import ServantBot


class TeamPredictHandler(BaseHandler):
    def __init__(self, bot: "ServantBot", context: "Context", team_name: str) -> None:
        super().__init__(bot, context, team_name, "team_info_handler")
        self.base_weight = [[10000.0 for _ in range(5)] for _ in range(5)]
        self.multiple = 0.1

    async def run(self):
        await self.update_team_name()
        self.message_id = await self.db.get_message_id(self.guild.name, self.team_name)
        if self.message_id is None:
            await self.handle_no_team()
            return
        self.members = await self.db.get_members(self.guild.name, self.team_name)
        if len(self.members) == 5:
            await self.predict()
        else:
            await self.handle_no_rank_member()

    async def predict(self) -> None:
        weight = await self.get_weight()
        members = [self.guild.get_member(member) for member in self.members]
        members = [member for member in members if member is not None]
        embed = discord.Embed(
            title="라인 예측",
            description="라인을 예측했어요.",
            color=0xBEBEFE,
        )
        for i, m in enumerate(weight):
            member = members[i]
            weight_sum = sum(m)
            percent = [f"{int(w/weight_sum*100)}%" for w in m]
            embed.add_field(
                name=f"{member.mention}",
                value=f"`TOP:`**{percent[0]}** `JG:`**{percent[1]}** `MID:`**{percent[2]}** `BOT:`**{percent[3]}** `SUP:`**{percent[4]}**",
                inline=False,
            )
        await self.context.send(embed=embed, ephemeral=True, silent=True)

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

    async def handle_no_rank_member(self):
        embed = discord.Embed(
            title="팀 인원이 5명이 아닙니다.",
            description="팀 인원을 확인해 주세요.",
            color=0xE02B2B,
        )
        await self.context.send(embed=embed, ephemeral=True, silent=True)
        self.logger.warning(
            f"{self.context.author.name} tried to shuffle team with wrong member number."
        )
