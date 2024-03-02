import traceback
from typing import TYPE_CHECKING

import discord

from database import TeamDataManager
from utils.logger import get_logger

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import ServantBot


class BaseHandler:
    def __init__(
        self,
        bot: "ServantBot",
        context: "Context",
        team_name: str,
        logger_name: str,
    ) -> None:
        self.bot = bot
        self.context = context
        if context.guild is None:
            raise ValueError("Guild is not found.")
        self.guild = context.guild
        self.author = context.author
        self.channel = context.channel
        self.team_name = team_name
        self.db = TeamDataManager(bot)
        self.logger = get_logger(logger_name)

    async def run(self):
        raise NotImplementedError

    async def update_team_name(self):
        try:
            if self.team_name == "":
                self.team_name = await self.db.get_team_name(self.guild.name)
        except Exception:
            self.logger.error("Error occurred while getting team name.")
            self.logger.debug(traceback.format_exc())
            self.team_name = ""

    async def handle_no_team(self):
        embed = discord.Embed(
            title="팀이 생성되지 않았어요.",
            description="**/q**로 팀을 먼저 생성해 주세요.",
            color=0xE02B2B,
        )
        await self.context.send(embed=embed, ephemeral=True, silent=True)
        self.logger.warning(
            f"{self.author} (ID: {self.author.id}) tried to interact a team that does not exist."
        )
