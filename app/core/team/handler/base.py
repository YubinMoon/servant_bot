import traceback
from typing import TYPE_CHECKING

from discord.ext import commands

from ....common.logger import get_logger
from ...database import TeamDataManager
from ...error.team import NoTeamError, TeamBaseError

if TYPE_CHECKING:
    from bot import ServantBot
    from discord import Embed
    from discord.ext.commands import Context


class BaseHandler:
    logger_name = "base_handler"

    def __init__(
        self,
        bot: "ServantBot|None",
        context: "Context",
        team_name: str,
    ) -> None:
        if context.guild is None:
            raise commands.GuildNotFound("This command is not available in DM.")
        self.bot = bot
        self.context = context
        self.guild = context.guild
        self.author = context.author
        self.channel = context.channel
        self.team_name = team_name
        self.db = TeamDataManager(self.guild, team_name)
        self.logger = get_logger(self.logger_name)

    async def run(self) -> None:
        try:
            await self.check_team_name()
            await self.action()
        except TeamBaseError as e:
            await self.send_error_message(e.get_embed())
            self.logger.error(e)
            traceback.print_exc()

    async def check_team_name(self):
        if self.team_name == "":
            team_name = await self.db.get_team_name()
            if team_name is None:
                self.logger.error("There is no team.")
                raise NoTeamError("There is no team.")
            self.team_name = team_name
            self.db = TeamDataManager(self.guild, self.team_name)

    async def action(self) -> None:
        raise NotImplementedError

    async def send_error_message(self, embed: "Embed") -> None:
        await self.context.send(embed=embed, ephemeral=True, silent=True)
