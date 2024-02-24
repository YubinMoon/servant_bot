import discord
from discord.ext.commands import Context

from bot import ServantBot

from .base import BaseHandler


class TeamInfoHandler(BaseHandler):
    def __init__(
        self, bot: ServantBot, context: Context, team_name: str | None
    ) -> None:
        super().__init__(bot, context, team_name, "team_info_handler")

    async def run(self):
        await self.update_team_name()
        self.message_id = await self.db.get_message_id(self.guild.name, self.team_name)
        if self.message_id is None:
            await self.handle_no_team()
            return
        self.members = await self.db.get_members(self.guild.name, self.team_name)
        members = [self.guild.get_member(member) for member in self.members]
        embed = discord.Embed(
            color=0xBEBEFE,
        )
        embed.add_field(
            name=f"현재 팀원: {len(members)}",
            value="\n".join(
                [f"{member.mention} ({member.name})" for member in members]
            ),
        )
        await self.context.send(embed=embed, ephemeral=True, silent=True)
