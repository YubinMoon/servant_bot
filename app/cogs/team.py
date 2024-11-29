from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands
from regex import F

from ..common.logger import get_logger
from ..core.database import get_session
from ..core.error.team import TeamBaseError
from ..core.team import controller, handler
from ..core.team.view import (
    JoinTeamView,
    TeamControlView,
    TeamInfoView,
    TeamJoinView,
    TeamLeftView,
    TeamShuffleView,
)

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
    @commands.hybrid_command(
        name="q", description="새로운 팀 생성", aliases=["ㅋ", "큐"]
    )
    @app_commands.describe(name="팀 이름")
    async def alias_start(self, context: "Context", name: str) -> None:
        await self.start(context, name)

    @commands.guild_only()
    @team.command(name="start", description="새로운 팀 생성")
    @app_commands.describe(name="팀 이름")
    async def start(self, context: "Context", name: str) -> None:
        with get_session() as session:
            message_id = await controller.setup_embed(context, name)
            team = await handler.create_team(session, message_id, name)
            logger.info(f"created new team: {team.name} ({message_id})")
            await handler.add_member(
                session,
                team,
                context.author.id,
                context.author.name,
            )
            message = await controller.fetch_message(context, team)
            await controller.send_join_alert(
                message,
                team,
                context.author.id,
            )
            await controller.update_team_message(
                message,
                team,
                JoinTeamView(team),
            )
            logger.info(
                f"{context.author.name} (ID: {context.author.id}) joined the team {team.name} (ID: {team.id})."
            )

    @commands.guild_only()
    @commands.hybrid_command(
        name="j",
        description="alias of /team join",
        aliases=["ㅊ", "참", "참여", "참가"],
    )
    async def alias_join(self, context: "Context") -> None:
        await self.join(context)

    @commands.guild_only()
    @team.command(name="join", description="생성된 팀에 참가")
    async def join(self, context: "Context") -> None:
        with get_session() as session:
            teams = handler.get_team_list(session)
            if len(teams) == 1:
                team = teams[0]
                await handler.add_member(
                    session,
                    team,
                    context.author.id,
                    context.author.name,
                )
                message = await controller.fetch_message(context.channel, team)
                await controller.send_join_alert(
                    message,
                    team,
                    context.author.id,
                )
                await controller.update_team_message(
                    message,
                    team,
                    JoinTeamView(team),
                )
                logger.info(
                    f"{context.author.name} (ID: {context.author.id}) joined the team {team.name} (ID: {team.id})."
                )
                await context.send(
                    f"{team.name} 팀에 참가했어요.",
                    ephemeral=True,
                    delete_after=3,
                )
            else:
                view = TeamJoinView(teams)
                await context.send(
                    "참가하려는 팀을 선택해 주세요.",
                    view=view,
                    ephemeral=True,
                    delete_after=10,
                )

    @commands.guild_only()
    @commands.hybrid_command(
        name="c",
        description="alias of /team cancel",
        aliases=["ㅊㅅ", "취", "취소"],
    )
    async def alias_cencel_join(self, context: "Context") -> None:
        await self.cancel_join(context)

    @commands.guild_only()
    @team.command(name="cancel", description="팀 참가 취소")
    async def cancel_join(self, context: "Context") -> None:
        with get_session() as session:
            teams = handler.get_team_list(session)
            if len(teams) == 1:
                team = teams[0]
                await handler.remove_member(
                    session,
                    team,
                    context.author.id,
                    context.author.name,
                )
                message = await controller.fetch_message(context.channel, team)
                await controller.send_left_alert(
                    message,
                    team,
                    context.author.id,
                )
                await controller.update_team_message(
                    message,
                    team,
                    JoinTeamView(team),
                )
                logger.info(
                    f"{context.author.name} (ID: {context.author.id}) left the team {team.name} (ID: {team.id})."
                )
                await context.send(
                    f"{team.name} 팀에서 나갔어요.",
                    ephemeral=True,
                    delete_after=3,
                )
            else:
                view = TeamLeftView(teams)
                await context.send(
                    "나가려는 팀을 선택해 주세요.",
                    view=view,
                    ephemeral=True,
                    delete_after=10,
                )

    @commands.guild_only()
    @commands.hybrid_command(
        name="t",
        description="alias of /team info",
        aliases=["ㅌ", "팀", "팀확인"],
    )
    async def alias_info(self, context: "Context") -> None:
        await self.info(context)

    @commands.guild_only()
    @team.command(name="info", description="팀 확인")
    async def info(self, context: "Context") -> None:
        with get_session() as session:
            teams = handler.get_team_list(session)
            if len(teams) == 1:
                team = teams[0]
                with get_session() as session:
                    message = await controller.fetch_message(context.channel, team)
                    await controller.show_team_detail(message, team)
                    view = TeamControlView(team)
                    await context.send(
                        f"**{team.name}**팀 메뉴", view=view, ephemeral=True
                    )
            else:
                await controller.show_team_list(context, teams, TeamInfoView(teams))

    @commands.guild_only()
    @commands.hybrid_command(
        name="s",
        description="alias of /team shuffle",
        aliases=["ㅅ", "셔", "셔플", "r", "random"],
    )
    async def alias_shuffle(self, context: "Context") -> None:
        await self.shuffle(context)

    @commands.guild_only()
    @team.command(name="shuffle", description="랜덤 팀 생성")
    async def shuffle(self, context: "Context") -> None:
        with get_session() as session:
            teams = handler.get_team_list(session)
            if len(teams) == 1:
                team = teams[0]
                message = await controller.fetch_message(context.channel, team)
                members = team.members

                team_idx = await handler.get_random_team(session, team)
                if len(members) == 5:
                    await controller.send_rank_team(message, team, team_idx)
                else:
                    await controller.send_custom_team(message, team, team_idx)
                await context.send(
                    f"{team.name} 팀을 섞었어요.",
                    ephemeral=True,
                    delete_after=3,
                )
            else:
                view = TeamShuffleView(teams)
                await context.send(
                    "참가하려는 팀을 선택해 주세요.",
                    view=view,
                    ephemeral=True,
                    delete_after=10,
                )

    @commands.Cog.listener()
    async def on_command_error(self, context: "Context", error) -> None:
        if isinstance(error, TeamBaseError):
            if error.alert:
                embed = error.get_embed()
                await context.send(embed=embed, ephemeral=True)
            logger.warning(f"{context.author} (ID: {context.author.id}) raised {error}")
        elif isinstance(error, commands.errors.CommandError):
            logger.error(f"{context.author} (ID: {context.author.id}) raised {error}")
