from typing import TYPE_CHECKING

from database import TeamDataManager
from utils.logger import get_logger

from .error import NoTeamError, TeamBaseError

if TYPE_CHECKING:
    from discord import Embed
    from discord.ext.commands import Context

    from bot import ServantBot


class BaseHandler:
    logger_name = "base_handler"

    def __init__(
        self,
        bot: "ServantBot",
        context: "Context",
        team_name: str,
    ) -> None:
        if context.guild is None:
            raise ValueError("Guild is not found.")

        self.bot = bot
        self.context = context
        self.guild = context.guild
        self.author = context.author
        self.channel = context.channel
        self.team_name = team_name
        self.db = TeamDataManager(bot)
        self.logger = get_logger(self.logger_name)

    async def run(self) -> None:
        try:
            await self.check_team_name()
            await self.action()
        except TeamBaseError as e:
            await self.send_error_message(e.get_embed())
            self.logger.error(e)

    async def check_team_name(self):
        if self.team_name == "":
            team_name = await self.db.get_team_name(self.guild.name)
            if team_name is None:
                self.logger.error("There is no team.")
                raise NoTeamError("There is no team.")
            self.team_name = team_name

    async def action(self) -> None:
        raise NotImplementedError

    async def send_error_message(self, embed: "Embed") -> None:
        await self.context.send(embed=embed, ephemeral=True, silent=True)
