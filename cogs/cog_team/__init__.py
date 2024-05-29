from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils.command import get_group_command_description
from utils.hash import get_random_key
from utils.logger import get_logger

from .handler import (
    CancelTeamHandler,
    JoinTeamHandler,
    NewTeamHandler,
    ShuffleTeamHandler,
    TeamInfoHandler,
    TeamPredictHandler,
)

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import ServantBot


class Team(commands.Cog, name="team"):
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot
        self.logger = get_logger("team")

    @commands.guild_only()
    @commands.hybrid_group(name="team")
    async def team(self, context: "Context") -> None:
        prefix: str = self.bot.config["prefix"]
        embed = discord.Embed(
            description="명령어 리스트",
            color=0xBEBEFE,
        )
        cog_commands = self.get_commands()
        data = []
        for group_command in cog_commands:
            if (
                isinstance(group_command, commands.core.Group)
                and group_command.name == "team"
            ):
                for command in group_command.commands:
                    data.append(get_group_command_description(prefix, "team", command))
        help_text = "\n".join(data)
        embed.add_field(name="Team", value=f"```{help_text}```", inline=False)
        await context.send(embed=embed, ephemeral=True)

    @commands.guild_only()
    @team.command(name="start", description="새로운 팀 생성")
    @app_commands.describe(name="팀 이름")
    async def start(self, context: "Context", name: str = "") -> None:
        if name == "":
            name = get_random_key(6)
        await NewTeamHandler(self.bot, context, name).run()
        await JoinTeamHandler(self.bot, context, name).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="q", description="새로운 팀 생성", aliases=["ㅋ", "큐"]
    )
    @app_commands.describe(name="팀 이름")
    async def alias_start(self, context: "Context", name: str = "") -> None:
        await self.start(context, name)

    @commands.guild_only()
    @team.command(name="join", description="생성된 팀에 참가")
    @app_commands.describe(name="팀 이름")
    async def join(self, context: "Context", name: str = "") -> None:
        await JoinTeamHandler(self.bot, context, name).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="j",
        description="alias of /team join",
        aliases=["ㅊ", "참", "참여", "참가"],
    )
    @app_commands.describe(name="팀 이름")
    async def alias_join(self, context: "Context", name: str = "") -> None:
        await self.join(context, name)

    @commands.guild_only()
    @team.command(name="cancel", description="팀 참가 취소")
    @app_commands.describe(name="팀 이름")
    async def cancel_join(self, context: "Context", name: str = "") -> None:
        await CancelTeamHandler(self.bot, context, name).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="c",
        description="alias of /team cancel",
        aliases=["ㅊㅅ", "취", "취소"],
    )
    @app_commands.describe(name="팀 이름")
    async def alias_cencel_join(self, context: "Context", name: str = "") -> None:
        await self.cancel_join(context, name)

    @commands.guild_only()
    @team.command(name="shuffle", description="랜덤 팀 생성")
    @app_commands.describe(name="팀 이름")
    async def shuffle(self, context: "Context", name: str = "") -> None:
        await ShuffleTeamHandler(self.bot, context, name).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="s",
        description="alias of /team shuffle",
        aliases=["ㅅ", "셔", "셔플", "r", "random"],
    )
    @app_commands.describe(name="팀 이름")
    async def alias_shuffle(self, context: "Context", name: str = "") -> None:
        await self.shuffle(context, name)

    @commands.guild_only()
    @team.command(name="info", description="팀 확인")
    @app_commands.describe(name="팀 이름")
    async def info(self, context: "Context", name: str = "") -> None:
        await TeamInfoHandler(self.bot, context, name).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="t",
        description="alias of /team info",
        aliases=["ㅌ", "팀", "팀확인"],
    )
    @app_commands.describe(name="팀 이름")
    async def alias_info(self, context: "Context", name: str = "") -> None:
        await self.info(context, name)

    @commands.guild_only()
    @team.command(name="predict", description="팀 예측")
    @app_commands.describe(name="팀 이름")
    async def predict(self, context: "Context", name: str = "") -> None:
        await TeamPredictHandler(self.bot, context, name).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="p",
        description="alias of /team predict",
        aliases=["ㅂ", "예", "예측"],
    )
    @app_commands.describe(name="팀 이름")
    async def alias_predict(self, context: "Context", name: str = "") -> None:
        await self.predict(context, name)


async def setup(bot: "ServantBot") -> None:
    await bot.add_cog(Team(bot))
