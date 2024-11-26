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


class NoTeamError(TeamBaseError):
    def __init__(self, message: str, team_name: str = ""):
        super().__init__(message)
        self.team_name = team_name

    def get_embed(self):
        title = "팀이 생성되지 않았어요."
        if self.team_name:
            title = f"**{self.team_name}** 팀이 생성되지 않았어요."
        embed = Embed(
            title=title,
            description="**/q**로 팀을 먼저 생성해 주세요.",
            color=Colors.ERROR,
        )
        return embed


class NoTeamSelectError(TeamBaseError):
    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(message)

    def get_embed(self):
        title = "팀이 선택되지 않았어요."
        embed = Embed(
            title=title,
            description="**/j**로 팀을 먼저 선택해 주세요.",
            color=Colors.ERROR,
        )
        return embed


class NoTeamMessageError(TeamBaseError):
    def __init__(self, message: str, team_name: str = ""):
        super().__init__(message)
        self.team_name = team_name

    def get_embed(self):
        title = "팀 메시지가 없어요."
        if self.team_name:
            title = f"**{self.team_name}** 팀 메시지가 없어요."
        embed = Embed(
            title=title,
            description="**/q**로 팀을 다시 생성해 주세요.",
            color=Colors.ERROR,
        )
        return embed


class NoMemberError(TeamBaseError):
    def __init__(self, message: str, team_name: str = ""):
        super().__init__(message)
        self.team_name = team_name

    def get_embed(self):
        title = "팀에 아무도 참가하지 않았어요."
        if self.team_name:
            title = f"**{self.team_name}** 팀에 아무도 참가하지 않았어요."
        embed = Embed(
            title=title,
            description="**/j**로 팀에 먼저 참가해 주세요.",
            color=Colors.ERROR,
        )
        return embed


class AlreadyInTeamError(TeamBaseError):
    def __init__(self, message: str, team_name: str = ""):
        super().__init__(message)
        self.team_name = team_name

    def get_embed(self):
        title = "이미 팀에 참가하고 있어요."
        if self.team_name:
            title = f"이미 **{self.team_name}** 팀에 참가하고 있어요."
        embed = Embed(
            title=title,
            description="팀을 떠나려면 **/c**로 취소해 주세요.",
            color=Colors.ERROR,
        )
        return embed


class AlreadyOutTeamError(TeamBaseError):
    def __init__(self, message: str, team_name: str = ""):
        super().__init__(message)
        self.team_name = team_name

    def get_embed(self):
        title = "팀에 참가하지 않았어요."
        if self.team_name:
            title = f"**{self.team_name}** 팀에 참가하지 않았어요."
        embed = Embed(
            title=title,
            description="팀에 참가하려면 **/j**로 참가해 주세요.",
            color=Colors.ERROR,
        )
        return embed


class MemberNumError(TeamBaseError):
    def __init__(self, message: str, team_name: str = ""):
        super().__init__(message)
        self.team_name = team_name

    def get_embed(self):
        title = "팀에 참가한 맴버가 맞지 않아요."
        if self.team_name:
            title = f"**{self.team_name}** 팀에 참가한 맴버가 맞지 않아요."
        embed = Embed(
            title=title,
            description="팀 인원을 5명 또는 10명으로 맞춰주세요.",
            color=Colors.ERROR,
        )
        return embed


class RankMemberNumError(TeamBaseError):
    def __init__(self, message: str, team_name: str = ""):
        super().__init__(message)
        self.team_name = team_name

    def get_embed(self):
        title = "팀에 참가한 맴버가 맞지 않아요."
        if self.team_name:
            title = f"**{self.team_name}** 팀에 참가한 맴버가 맞지 않아요."
        embed = Embed(
            title=title,
            description="팀 인원을 5명으로 맞춰주세요.",
            color=Colors.ERROR,
        )
        return embed
