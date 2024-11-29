import discord
from discord import app_commands


def base_autocomplete(scopes: list[str]):
    async def autocomplete(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=scope, value=scope)
            for scope in scopes
            if current.lower() in scope.lower()
        ]

    return autocomplete
