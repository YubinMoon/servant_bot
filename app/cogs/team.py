from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from ..common.logger import get_logger
from ..core.database import get_session
from ..core.error.team import TeamBaseError
from ..core.team import controller
from ..core.team.controller import (
    CancelTeamController,
    JoinTeamController,
    ShuffleTeamController,
    TeamInfoController,
)
from ..core.team.handler import (
    JoinTeamHandler,
    NewTeamHandler,
    ShuffleTeamHandler,
    TeamInfoHandler,
    join,
    new,
)
from ..core.team.handler.cancel import CancelTeamHandler

if TYPE_CHECKING:
    from bot import ServantBot
    from discord.ext.commands import Context

logger = get_logger(__name__)


class Team(commands.Cog, name="team"):
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot

    @commands.guild_only()
    @commands.hybrid_group(name="team", fallback="get")
    async def team(self, context: "Context") -> None:
        pass

    @commands.guild_only()
    @team.command(name="start", description="새로운 팀 생성")
    @app_commands.describe(name="팀 이름")
    async def start(self, context: "Context", name: str) -> None:
        with get_session() as session:
            message_id = await controller.setup_embed(context, name)
            team = await new.create_team(session, message_id, name)
            logger.info(f"created new team: {team.name} ({message_id})")
            await join.add_member(
                session,
                team,
                context.author.id,
                context.author.name,
            )
            await controller.update_message(context, team)
            logger.info(
                f"{context.author.name} (ID: {context.author.id}) joined the team {team.name} (ID: {team.id})."
            )

    @commands.guild_only()
    @commands.hybrid_command(
        name="q", description="새로운 팀 생성", aliases=["ㅋ", "큐"]
    )
    @app_commands.describe(name="팀 이름")
    async def alias_start(self, context: "Context", name: str) -> None:
        await self.start(context, name)

    @commands.guild_only()
    @team.command(name="join", description="생성된 팀에 참가")
    async def join(self, context: "Context") -> None:
        with get_session() as session:
            controller = JoinTeamController(context)
            await JoinTeamHandler(session, controller).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="j",
        description="alias of /team join",
        aliases=["ㅊ", "참", "참여", "참가"],
    )
    async def alias_join(self, context: "Context") -> None:
        await self.join(context)

    @commands.guild_only()
    @team.command(name="cancel", description="팀 참가 취소")
    async def cancel_join(self, context: "Context") -> None:
        with get_session() as session:
            controller = CancelTeamController(context)
            await CancelTeamHandler(session, controller).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="c",
        description="alias of /team cancel",
        aliases=["ㅊㅅ", "취", "취소"],
    )
    async def alias_cencel_join(self, context: "Context") -> None:
        await self.cancel_join(context)

    @commands.guild_only()
    @team.command(name="shuffle", description="랜덤 팀 생성")
    async def shuffle(self, context: "Context") -> None:
        with get_session() as session:
            controller = ShuffleTeamController(context)
            await ShuffleTeamHandler(session, controller).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="s",
        description="alias of /team shuffle",
        aliases=["ㅅ", "셔", "셔플", "r", "random"],
    )
    async def alias_shuffle(self, context: "Context") -> None:
        await self.shuffle(context)

    @commands.guild_only()
    @team.command(name="info", description="팀 확인")
    async def info(self, context: "Context") -> None:
        with get_session() as session:
            controller = TeamInfoController(context)
            await TeamInfoHandler(session, controller).run()

    @commands.guild_only()
    @commands.hybrid_command(
        name="t",
        description="alias of /team info",
        aliases=["ㅌ", "팀", "팀확인"],
    )
    async def alias_info(self, context: "Context") -> None:
        await self.info(context)

    @commands.Cog.listener()
    async def on_command_error(self, context: "Context", error) -> None:
        if isinstance(error, TeamBaseError):
            if error.alert:
                embed = error.get_embed()
                await context.send(embed=embed, ephemeral=True)
            logger.warning(f"{context.author} (ID: {context.author.id}) raised {error}")
        elif isinstance(error, commands.errors.CommandError):
            logger.error(f"{context.author} (ID: {context.author.id}) raised {error}")
