from typing import TYPE_CHECKING

from discord import Embed

from .base import BaseHandler

if TYPE_CHECKING:
    from discord import Message
    from discord.ext.commands import Context

    from bot import ServantBot


class NewTeamHandler(BaseHandler):
    logger_name = "new_team_handler"

    def __init__(
        self, bot: "ServantBot", context: "Context", team_name: str = ""
    ) -> None:
        super().__init__(bot, context, team_name)

    async def action(self):
        message = await self.setup_embed()
        await self.db.new_team(self.guild.name, message.id, self.team_name)
        self.logger.info(f"created new team: {self.team_name} ({message.id})")

    async def setup_embed(self) -> "Message":
        embed = Embed(
            title=f"{self.team_name} 팀이 구성되었어요.",
            description="**/j**로 등록... 하든가 말든가",
            color=0xBEBEFE,
        )
        embed.add_field(name=f"현제 인원: 0", value="")
        embed.set_footer(text="/s로 굴릴 수 있어요. /c로 팀 등록을 취소할 수 있어요.")
        message = await self.context.send(embed=embed, silent=True)
        return message
