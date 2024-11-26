import discord
from discord import ui

from ..database import get_session
from ..model.team import Team
from .handler import join


class JoinTeamView(ui.View):
    def __init__(self, team: Team):
        super().__init__(timeout=None)
        self.team = team

    @ui.button(label="참가", style=discord.ButtonStyle.success)
    async def join(self, button: ui.Button, interaction: discord.Interaction):
        pass


class JoinTeamButton(ui.Button["JoinTeamSelectView"]):
    def __init__(self, team: Team, user_id: int):
        super().__init__(
            label=team.name if len(team.name) < 10 else team.name[:10] + "...",
            style=discord.ButtonStyle.success,
        )
        self.team = team

        ids = [member.discord_id for member in team.members]
        if user_id in ids:
            self.disabled = True
            self.style = discord.ButtonStyle.grey

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_team = self.team
        await interaction.response.defer()
        self.view.stop()


class JoinTeamSelectView(ui.View):
    def __init__(self, teams: list[Team], user_id: int):
        super().__init__(timeout=10)
        self.selected_team: str | None = None
        for team in teams:
            self.add_item(item=JoinTeamButton(team, user_id))


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
