from typing import Optional

from discord import Embed
from discord.ext.commands import CommandError

from ...common.utils.color import Colors


class TeamBaseError(CommandError):
    def __init__(self, message: str, alert: bool = True):
        super().__init__(message)
        self.message = message
        self.alert = alert

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"

    def get_embed(self):
        raise NotImplementedError


class TeamError(TeamBaseError):
    def __init__(
        self,
        title: str,
        display_title: Optional[str] = None,
        description: Optional[str] = None,
        alert: bool = True,
    ):
        super().__init__(title, alert)
        self.title = title
        self.display_title = display_title or title
        self.description = description

    def get_embed(self):
        embed = Embed(
            title=self.display_title,
            description=self.description,
            color=Colors.ERROR,
        )
        return embed
