import discord
from discord.ext.commands import Context

from bot import ServantBot

from .base import BaseHandler


class CancelTeamHandler(BaseHandler):
    def __init__(
        self, bot: ServantBot, context: Context, team_name: str | None
    ) -> None:
        super().__init__(bot, context, team_name, "cancel_team_handler")

    async def run(self):
        await self.update_team_name()
        self.message_id = await self.db.get_message_id(self.guild.name, self.team_name)
        if self.message_id is None:
            await self.handle_no_team()
            return
        self.members = await self.db.get_members(self.guild.name, self.team_name)
        if self.author.id not in self.members:
            await self.handle_not_a_member()
            return
        index = self.members.index(self.author.id)
        await self.db.pop_member(self.guild.name, self.team_name, index)
        await self.update_message()

        embed = discord.Embed(
            description=f"{self.author.mention}님이 팀 등록을 취소했어요.",
            color=0xBEBEFE,
        )
        await self.context.send(embed=embed, silent=True)

    async def update_message(self) -> None:
        message = await self.channel.fetch_message(self.message_id)
        self.members = await self.db.get_members(self.guild.name, self.team_name)
        embed = message.embeds[0]
        embed.set_field_at(
            index=0,
            name=f"현제 인원: {len(self.members)}",
            value=" - ".join([f"<@{member_id}>" for member_id in self.members]),
        )
        await message.edit(embed=embed)

    async def handle_not_a_member(self):
        embed = discord.Embed(
            title="팀에 참가하지 않았어요.",
            description="**/j**로 팀에 먼저 참가해 주세요.",
            color=0xE02B2B,
        )
        await self.context.send(embed=embed, ephemeral=True, silent=True)
        self.logger.warning(
            f"{self.author} (ID: {self.author.id}) tried to cancel joining a team that the user is not in."
        )
