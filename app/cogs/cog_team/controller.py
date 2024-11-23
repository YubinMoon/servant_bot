from typing import TYPE_CHECKING

from discord import Embed, NotFound

from error.team import NoTeamMessageError, NoTeamSelectError
from model.team import Team
from utils.color import Colors

if TYPE_CHECKING:
    from discord.ext.commands import Context
    from discord import Message

from .view import JoinTeamSelectView


class BaseController:
    pass


class NewTeamController(BaseController):
    def __init__(self, context: "Context") -> None:
        self.context = context

    async def setup_embed(self, name: str) -> int:
        embed = Embed(
            title=f"{name} 팀이 구성되었어요.",
            description="**/j**로 참여... 하든가 말든가",
            color=Colors.BASE,
        )
        embed.add_field(name=f"현제 인원: 0", value="")
        embed.set_footer(text="/s로 굴릴 수 있어요. /c로 팀 등록을 취소할 수 있어요.")
        message = await self.context.send(embed=embed, silent=True)
        return message.id


class JoinTeamController(BaseController):
    def __init__(self, context: "Context") -> None:
        self.context = context
        self.user_id = context.author.id
        self.user_name = context.author.name

        self._author = context.author

    async def get_team_name_from_view(self, teams: list[Team]) -> Team | None:
        view = JoinTeamSelectView(teams, self.user_id)
        message = await self.context.send(
            "참가하려는 팀을 선택해 주세요.", view=view, ephemeral=True
        )
        result = await view.wait()
        if result:
            await message.edit(content="팀을 선택하지 않았어요.", delete_after=5)
            return None
        return view.selected_team

    async def update_message(self, team: Team):
        message = await self._get_message(team)
        await self._refresh_message(team, message)
        await self._notify(team, message)

    async def _get_message(self, team: Team) -> "Message":
        message_id = team.message_id
        try:
            message = await self.context.channel.fetch_message(message_id)
        except NotFound as e:
            raise NoTeamMessageError("Team Create message is not found.", team.name)
        return message

    async def _refresh_message(self, team: Team, message: "Message") -> None:
        members = team.members
        if message.embeds == []:
            raise NoTeamMessageError("Team Create embed is not found.", team.name)
        embed = message.embeds[0]
        embed.set_field_at(
            index=0,
            name=f"현제 인원: {len(members)}",
            value=" - ".join([f"<@{member.discord_id}>" for member in members]),
        )
        print(f"현제 인원: {len(members)}")
        await message.edit(embed=embed)

    async def _notify(self, team: Team, message: "Message"):
        embed = Embed(
            description=f"{self._author.mention}님이 **{team.name}**팀에 참가했어요. {message.jump_url}",
            color=Colors.BASE,
        )
        await self.context.channel.send(embed=embed)
