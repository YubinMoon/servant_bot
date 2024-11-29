import discord
from discord import ui
from sqlmodel import Session

from ...common.logger import get_logger
from ..database import get_session
from ..error.team import TeamBaseError
from ..model.team import Team
from . import controller, handler

logger = get_logger(__name__)


class BaseTeamView(ui.View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item: ui.Item
    ):
        if isinstance(error, TeamBaseError):
            if error.alert:
                embed = error.get_embed()
                await interaction.followup.send(embed=embed, ephemeral=True)
            logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) raised {error}"
            )
        else:
            logger.info("timeout")
            raise error


class JoinTeamView(BaseTeamView):
    def __init__(self, team: Team):
        super().__init__(timeout=None)
        self.team = team

    @ui.button(label="참가", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        with get_session() as session:
            await join_team(session, interaction, self.team)


class TeamJoinView(BaseTeamView):
    def __init__(self, teams: list[Team]):
        super().__init__(timeout=10)
        for team in teams:
            self.add_item(item=self.TeamButton(team))

    class TeamButton(ui.Button["TeamJoinView"]):
        def __init__(self, team: Team):
            super().__init__(
                label=team.name if len(team.name) < 10 else team.name[:10] + "...",
                style=discord.ButtonStyle.primary,
            )
            self.team = team

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            with get_session() as session:
                await join_team(session, interaction, self.team)


class TeamLeftView(BaseTeamView):
    def __init__(self, teams: list[Team]):
        super().__init__(timeout=10)
        for team in teams:
            self.add_item(item=self.TeamButton(team))

    class TeamButton(ui.Button["TeamLeftView"]):
        def __init__(self, team: Team):
            super().__init__(
                label=team.name if len(team.name) < 10 else team.name[:10] + "...",
                style=discord.ButtonStyle.primary,
            )
            self.team = team

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            with get_session() as session:
                await left_team(session, interaction, self.team)


class TeamInfoView(BaseTeamView):
    def __init__(self, teams: list[Team]):
        super().__init__(timeout=10)
        for idx, team in enumerate(teams):
            self.add_item(item=self.TeamButton(idx + 1, team))

    class TeamButton(ui.Button["TeamInfoView"]):
        def __init__(self, idx: int, team: Team):
            super().__init__(
                label=str(idx),
                style=discord.ButtonStyle.primary,
            )
            self.team = team

        async def callback(self, interaction: discord.Interaction):
            with get_session() as session:
                self.team = session.get(Team, self.team.id)
                message = await controller.fetch_message(interaction.channel, self.team)
                await controller.show_team_detail(message, self.team)
                view = TeamControlView(self.team)
                await interaction.response.send_message(
                    f"**{self.team.name}**팀 메뉴", view=view, ephemeral=True
                )
                self.view.stop()


class TeamControlView(BaseTeamView):
    def __init__(self, team: Team):
        super().__init__(timeout=None)
        self.team = team

    @ui.button(label="참가", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        with get_session() as session:
            await join_team(session, interaction, self.team)

    @ui.button(label="떠나기", style=discord.ButtonStyle.secondary)
    async def left(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        with get_session() as session:
            await left_team(session, interaction, self.team)

    @ui.button(label="팀 섞기", style=discord.ButtonStyle.primary)
    async def shuffle(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        with get_session() as session:
            self.team = session.get(Team, self.team.id)
            message = await controller.fetch_message(interaction.channel, self.team)
            members = self.team.members

            team_idx = await handler.get_random_team(session, self.team)
            if len(members) == 5:
                await controller.send_rank_team(message, self.team, team_idx)
            else:
                await controller.send_custom_team(message, self.team, team_idx)

    @ui.button(label="팀 삭제", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        with get_session() as session:
            self.team = session.get(Team, self.team.id)
            message = await controller.fetch_message(interaction.channel, self.team)
            await handler.delete_team(session, self.team)
            await controller.send_delete_alert(message, self.team)
            logger.info(
                f"{interaction.user.name} (ID: {interaction.user.id}) deleted the team {self.team.name} (ID: {self.team.id})."
            )


class TeamShuffleView(BaseTeamView):
    def __init__(self, teams: list[Team]):
        super().__init__(timeout=10)
        for team in teams:
            self.add_item(item=self.TeamButton(team))

    class TeamButton(ui.Button["TeamShuffleView"]):
        def __init__(self, team: Team):
            super().__init__(
                label=team.name if len(team.name) < 10 else team.name[:10] + "...",
                style=discord.ButtonStyle.primary,
            )
            self.team = team

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            with get_session() as session:
                self.team = session.get(Team, self.team.id)
                message = await controller.fetch_message(interaction.channel, self.team)
                members = self.team.members

                team_idx = await handler.get_random_team(session, self.team)
                if len(members) == 5:
                    await controller.send_rank_team(message, self.team, team_idx)
                else:
                    await controller.send_custom_team(message, self.team, team_idx)


async def join_team(db: Session, interaction: "discord.Interaction", team: Team):
    team = db.get(Team, team.id)
    await handler.add_member(
        db,
        team,
        interaction.user.id,
        interaction.user.name,
    )
    message = await controller.fetch_message(interaction.channel, team)
    await controller.send_join_alert(
        message,
        team,
        interaction.user.id,
    )
    await controller.update_team_message(
        message,
        team,
        JoinTeamView(team),
    )
    logger.info(
        f"{interaction.user.name} (ID: {interaction.user.id}) joined the team {team.name} (ID: {team.id})."
    )


async def left_team(db: Session, interaction: "discord.Interaction", team: Team):
    team = db.get(Team, team.id)
    await handler.remove_member(
        db,
        team,
        interaction.user.id,
        interaction.user.name,
    )
    message = await controller.fetch_message(interaction.channel, team)
    await controller.send_left_alert(
        message,
        team,
        interaction.user.id,
    )
    await controller.update_team_message(
        message,
        team,
        JoinTeamView(team),
    )
    logger.info(
        f"{interaction.user.name} (ID: {interaction.user.id}) left the team {team.name} (ID: {team.id})."
    )
