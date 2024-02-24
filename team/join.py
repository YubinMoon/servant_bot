import discord
from discord.ext.commands import Context

from bot import ServantBot

from .base import BaseHandler


class JoinTeamHandler(BaseHandler):
    def __init__(
        self, bot: ServantBot, context: Context, team_name: str | None
    ) -> None:
        super().__init__(bot, context, team_name, "join_team_handler")

    async def run(self):
        await self.update_team_name()
        self.message_id = await self.db.get_message_id(self.guild.name, self.team_name)
        if self.message_id is None:
            await self.handle_no_team()
            return
        self.members = await self.db.get_members(self.guild.name, self.team_name)
        # if self.author.id in self.members:
        #     await self.handle_already_in_team()
        #     return
        await self.db.add_member(self.guild.name, self.team_name, self.author)
        await self.update_message()
        message = await self.channel.fetch_message(self.message_id)
        embed = discord.Embed(
            description=f"{self.author.mention}님이 **{self.team_name}**팀에 참가했어요. {message.jump_url}",
            color=0xBEBEFE,
        )
        await self.context.send(embed=embed)

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

    async def handle_already_in_team(self):
        embed = discord.Embed(
            title="이미 팀에 참가하고 있어요.",
            description="팀을 떠나려면 **/c**로 취소해 주세요.",
            color=0xE02B2B,
        )
        await self.context.send(embed=embed, ephemeral=True, silent=True)
        self.logger.warning(
            f"{self.author} (ID: {self.author.id}) tried to join a team that the user is already in."
        )
