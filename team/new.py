import traceback

import discord
from discord.ext.commands import Context

from bot import ServantBot

from .base import BaseHandler


class NewTeamHandler(BaseHandler):
    def __init__(self, bot: ServantBot, context: Context, team_name: str = "") -> None:
        super().__init__(bot, context, team_name, "new_team_handler")

    async def run(self):
        message = await self.setup_embed()
        try:
            await self.db.start_team(self.guild.name, message.id, self.team_name)
        except Exception:
            await self.handle_db_error(message)
        # await self.join(context)

    async def setup_embed(self) -> discord.Message:
        embed = discord.Embed(
            title=f"{self.team_name} 팀이 구성되었어요.",
            description="**/j**로 등록... 하든가 말든가",
            color=0xBEBEFE,
        )
        embed.add_field(name=f"현제 인원: 0", value="")
        embed.set_footer(text="/s로 굴릴 수 있어요. /c로 팀 등록을 취소할 수 있어요.")
        message = await self.context.send(embed=embed, silent=True)
        return message

    async def handle_db_error(self, message: discord.Message):
        self.logger.error("Error occurred while starting team.")
        self.logger.debug(traceback.format_exc())
        embed = discord.Embed(
            title="팀 생성에 실패했어요.",
            description="조금 쉬어야 할 것 같아요.",
            color=0xE02B2B,
        )
        await message.edit(embed=embed)

        error_embed = discord.Embed(
            title="ERROR LOG",
            description=f"```{traceback.format_exc()}```",
            color=0xE02B2B,
        )
        await self.context.send(embed=error_embed, ephemeral=True, silent=True)
