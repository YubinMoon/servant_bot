import discord
from discord import ui

from ...common.logger import get_logger
from ..database import get_session
from ..error.team import TeamBaseError, TeamError
from ..model.team import Team
from . import controller
from .handler import cancel, join, shuffle

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
            self.team = session.get(Team, self.team.id)
            await join.add_member(
                session,
                self.team,
                interaction.user.id,
                interaction.user.name,
            )
            message = await controller.fetch_message(interaction.channel, self.team)
            await controller.send_join_alert(
                message,
                self.team,
                interaction.user.id,
            )
            await controller.update_team_message(
                message,
                self.team,
                JoinTeamView(self.team),
            )
            logger.info(
                f"{interaction.user.name} (ID: {interaction.user.id}) joined the team {self.team.name} (ID: {self.team.id})."
            )


class BaseTeamSelectView(BaseTeamView):
    def __init__(self, teams: list[Team]):
        super().__init__(timeout=10)
        self.selected_team: str | None = None


class BaseTeamButton(ui.Button["BaseTeamSelectView"]):
    def __init__(
        self,
        team: Team,
        max_len=10,
        style: discord.ButtonStyle = discord.ButtonStyle.primary,
    ):
        super().__init__(
            label=team.name if len(team.name) < max_len else team.name[:10] + "...",
            style=style,
        )
        self.team = team

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_team = self.team
        self.view.stop()


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
                self.team = session.get(Team, self.team.id)
                await join.add_member(
                    session,
                    self.team,
                    interaction.user.id,
                    interaction.user.name,
                )
                message = await controller.fetch_message(interaction.channel, self.team)
                await controller.send_join_alert(
                    message,
                    self.team,
                    interaction.user.id,
                )
                await controller.update_team_message(
                    message,
                    self.team,
                    JoinTeamView(self.team),
                )
                logger.info(
                    f"{interaction.user.name} (ID: {interaction.user.id}) joined the team {self.team.name} (ID: {self.team.id})."
                )


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
                self.team = session.get(Team, self.team.id)
                await cancel.remove_member(
                    session,
                    self.team,
                    interaction.user.id,
                    interaction.user.name,
                )
                message = await controller.fetch_message(interaction.channel, self.team)
                await controller.send_left_alert(
                    message,
                    self.team,
                    interaction.user.id,
                )
                await controller.update_team_message(
                    message,
                    self.team,
                    JoinTeamView(self.team),
                )
                logger.info(
                    f"{interaction.user.name} (ID: {interaction.user.id}) left the team {self.team.name} (ID: {self.team.id})."
                )


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
                view = TeamDetailView(self.team)
                await interaction.response.send_message(
                    f"**{self.team.name}**팀 메뉴", view=view, ephemeral=True
                )
                self.view.stop()


class TeamDetailView(BaseTeamView):
    def __init__(self, team: Team):
        super().__init__(timeout=10)
        self.team = team

    @ui.button(label="참가", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        with get_session() as session:
            self.team = session.get(Team, self.team.id)
            await join.add_member(
                session,
                self.team,
                interaction.user.id,
                interaction.user.name,
            )
            message = await controller.fetch_message(interaction.channel, self.team)
            await controller.send_join_alert(
                message,
                self.team,
                interaction.user.id,
            )
            await controller.update_team_message(
                message,
                self.team,
                JoinTeamView(self.team),
            )
            logger.info(
                f"{interaction.user.name} (ID: {interaction.user.id}) joined the team {self.team.name} (ID: {self.team.id})."
            )

    @ui.button(label="떠나기", style=discord.ButtonStyle.danger)
    async def left(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        with get_session() as session:
            self.team = session.get(Team, self.team.id)
            await cancel.remove_member(
                session,
                self.team,
                interaction.user.id,
                interaction.user.name,
            )
            message = await controller.fetch_message(interaction.channel, self.team)
            await controller.send_left_alert(
                message,
                self.team,
                interaction.user.id,
            )
            await controller.update_team_message(
                message,
                self.team,
                JoinTeamView(self.team),
            )
            logger.info(
                f"{interaction.user.name} (ID: {interaction.user.id}) left the team {self.team.name} (ID: {self.team.id})."
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
                members = self.team.members

                team_idx = await shuffle.get_random_team(session, self.team)
                if len(members) == 5:
                    await controller.send_rank_team(session, self.team, team_idx)
                elif len(members) == 10:
                    await controller.send_custom_team(session, self.team, team_idx)


class CancelTeamButton(ui.Button["CancelTeamSelectView"]):
    def __init__(self, team: Team, user_id: int):
        super().__init__(
            label=team.name if len(team.name) < 10 else team.name[:10] + "...",
            style=discord.ButtonStyle.danger,
        )
        self.team = team

        ids = [member.discord_id for member in team.members]
        if user_id not in ids:
            self.disabled = True
            self.style = discord.ButtonStyle.grey

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_team = self.team
        await interaction.response.defer()
        self.view.stop()


class CancelTeamSelectView(ui.View):
    def __init__(self, teams: list[Team], user_id: int):
        super().__init__(timeout=10)
        self.selected_team: str | None = None
        for team in teams:
            self.add_item(item=CancelTeamButton(team, user_id))


class ShuffleTeamButton(ui.Button["ShuffleTeamSelectView"]):
    def __init__(self, team: Team):
        super().__init__(
            label=team.name if len(team.name) < 10 else team.name[:10] + "...",
            style=discord.ButtonStyle.danger,
        )
        self.team = team

        if len(team.members) not in [5, 10]:
            self.disabled = True
            self.style = discord.ButtonStyle.grey

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_team = self.team
        await interaction.response.defer()
        self.view.stop()


class ShuffleTeamSelectView(ui.View):
    def __init__(self, teams: list[Team], user_id: int):
        super().__init__(timeout=10)
        self.selected_team: str | None = None
        for team in teams:
            self.add_item(item=CancelTeamButton(team, user_id))


class TeamInfoButton(ui.Button["TeamInfoSelectView"]):
    def __init__(self, team: Team):
        super().__init__(
            label=team.name if len(team.name) < 10 else team.name[:10] + "...",
            style=discord.ButtonStyle.primary,
        )
        self.team = team

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_team = self.team
        await interaction.response.defer()
        self.view.stop()


class TeamInfoSelectView(ui.View):
    def __init__(self, teams: list[Team]):
        super().__init__(timeout=10)
        self.selected_team: str | None = None
        for team in teams:
            self.add_item(item=TeamInfoButton(team))
