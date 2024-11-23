import discord
from discord import ui

from model.team import Team


class TeamButton(ui.Button["JoinTeamSelectView"]):
    def __init__(self, team: Team, user_id: int):
        super().__init__(
            label=team.name,
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
            self.add_item(item=TeamButton(team, user_id))
