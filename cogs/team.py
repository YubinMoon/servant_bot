import logging
import random
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import Context

from database import TeamDataManager
from team import TeamHandler


class Team(commands.Cog, name="team"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.handler = TeamHandler(bot)
        self.logger: logging.Logger = bot.logger

    @commands.hybrid_group(name="team")
    async def team(self, context: Context) -> None:
        pass

    @team.command(name="start", description="새로운 팀 생성 (기존 팀 제거)")
    async def start(self, context: Context) -> None:
        try:
            await self.handler.start(context)
        except commands.CommandError as e:
            self.logger.warning(e)

    @commands.hybrid_command(
        name="q", description="alias of /team start", aliases=["ㅋ", "큐"]
    )
    async def alias_start(self, context: Context) -> None:
        await self.start(context)

    @team.command(name="join", description="생성된 팀에 참가")
    async def join(self, context: Context) -> None:
        try:
            await self.handler.join(context)
        except commands.CommandError as e:
            self.logger.warning(e)

    @commands.hybrid_command(
        name="j",
        description="alias of /team join",
        aliases=["ㅊ", "참", "참여", "참가"],
    )
    async def alias_join(self, context: Context) -> None:
        await self.join(context)

    @team.command(name="cancel", description="팀 참가 취소")
    async def cancel_join(self, context: Context) -> None:
        try:
            await self.handler.cancel_join(context)
        except commands.CommandError as e:
            self.logger.warning(e)

    @commands.hybrid_command(
        name="c",
        description="alias of /team cancel",
        aliases=["ㅊㅅ", "취", "취소"],
    )
    async def alias_cencel_join(self, context: Context) -> None:
        await self.cancel_join(context)

    @team.command(name="shuffle", description="랜덤 팀 생성")
    async def shuffle(self, context: Context) -> None:
        try:
            await self.handler.shuffle(context)
        except commands.CommandError as e:
            self.logger.warning(e)

    @commands.hybrid_command(
        name="s",
        description="alias of /team shuffle",
        aliases=["ㅅ", "셔", "셔플", "r", "random"],
    )
    async def alias_shuffle(self, context: Context) -> None:
        await self.shuffle(context)

    @team.command(name="info", description="팀 확인")
    async def info(self, context: Context) -> None:
        try:
            await self.handler.info(context)
        except commands.CommandError as e:
            self.logger.warning(e)

    @commands.hybrid_command(
        name="t",
        description="alias of /team info",
        aliases=["ㅌ", "팀", "팀확인"],
    )
    async def alias_info(self, context: Context) -> None:
        await self.info(context)


async def setup(bot) -> None:
    await bot.add_cog(Team(bot))
