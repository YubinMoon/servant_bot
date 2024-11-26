from typing import TYPE_CHECKING

from discord import Embed, NotFound

from ...common.utils.color import Colors
from ..error.team import NoTeamMessageError
from ..model.team import Member, Team

if TYPE_CHECKING:
    from discord.ext.commands import Context
    from discord import Message

from .view import (
    CancelTeamSelectView,
    JoinTeamSelectView,
    JoinTeamView,
    TeamInfoSelectView,
)


class BaseTeamController:
    def __init__(self, context: "Context") -> None:
        self.context = context

    async def send_error_message(self, embed: "Embed") -> None:
        await self.context.send(embed=embed, ephemeral=True, silent=True)


async def update_message(context: "Context", team: Team):
    message_id = team.message_id
    try:
        message = await context.channel.fetch_message(message_id)
    except NotFound as e:
        raise NoTeamMessageError("Team Create message is not found.", team.name)
    if message.embeds == []:
        raise NoTeamMessageError("Team Create embed is not found.", team.name)

    members = team.members
    embed = message.embeds[0]
    embed.set_field_at(
        index=0,
        name=f"현제 인원: {len(members)}",
        value=" - ".join([f"<@{member.discord_id}>" for member in members]),
    )
    await message.edit(embed=embed, view=JoinTeamView(team))

    embed = Embed(
        description=f"{context.author.mention}님이 **{team.name}**팀에 참가했어요.",
        color=Colors.BASE,
    )
    await message.reply(embed=embed)


class JoinTeamController(BaseTeamController):
    def __init__(self, context: "Context") -> None:
        super().__init__(context)
        self.user_id = context.author.id
        self.user_name = context.author.name
        self._author = context.author

    async def get_team_from_view(self, teams: list[Team]) -> Team | None:
        view = JoinTeamSelectView(teams, self.user_id)
        message = await self.context.send(
            "참가하려는 팀을 선택해 주세요.", view=view, ephemeral=True
        )
        result = await view.wait()
        if result:
            await message.edit(
                content="팀을 선택하지 않았어요.", view=None, delete_after=5
            )
            return None
        await message.delete()
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
        await message.edit(embed=embed)

    async def _notify(self, team: Team, message: "Message"):
        embed = Embed(
            description=f"{self._author.mention}님이 **{team.name}**팀에 참가했어요. {message.jump_url}",
            color=Colors.BASE,
        )
        await self.context.channel.send(embed=embed)


async def setup_embed(context: "Context", name: str) -> int:
    embed = Embed(
        title=f"{name} 팀이 구성되었어요.",
        description="**/j**로 참여... 하든가 말든가",
        color=Colors.BASE,
    )
    embed.add_field(name=f"현제 인원: 0", value="")
    embed.set_footer(text="/s로 굴릴 수 있어요. /c로 팀 등록을 취소할 수 있어요.")
    message = await context.send(embed=embed, silent=True)
    return message.id


class NewTeamController(JoinTeamController):
    def __init__(self, context: "Context") -> None:
        super().__init__(context)

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


class CancelTeamController(JoinTeamController):
    def __init__(self, context: "Context") -> None:
        super().__init__(context)

    async def get_team_from_view(self, teams: list[Team]) -> Team | None:
        view = CancelTeamSelectView(teams, self.user_id)
        message = await self.context.send(
            "나가려는 팀을 선택해 주세요.", view=view, ephemeral=True
        )
        result = await view.wait()
        if result:
            await message.edit(
                content="팀을 선택하지 않았어요.", view=None, delete_after=5
            )
            return None
        await message.delete()
        return view.selected_team

    async def _notify(self, team: Team, message: "Message"):
        embed = Embed(
            description=f"{self._author.mention}님이 **{team.name}**팀 참가를 취소했어요. {message.jump_url}",
            color=Colors.BASE,
        )
        await self.context.channel.send(embed=embed)


class ShuffleTeamController(JoinTeamController):
    def __init__(self, context: "Context") -> None:
        super().__init__(context)

    async def get_team_from_view(self, teams: list[Team]) -> Team | None:
        view = CancelTeamSelectView(teams, self.user_id)
        message = await self.context.send(
            "뽑을 팀을 선택해 주세요.", view=view, ephemeral=True
        )
        result = await view.wait()
        if result:
            await message.edit(
                content="팀을 선택하지 않았어요.", view=None, delete_after=5
            )
            return None
        await message.delete()
        return view.selected_team

    async def send_rank_team(self, team: Team, rank_team: list[int]) -> None:
        LANE = ["탑", "정글", "미드", "원딜", "서폿"]

        embed = Embed(
            title=f"{team.name} 팀",
            description="라인을 배정했어요.",
            color=Colors.BASE,
        )
        for l, m in enumerate(rank_team):
            member = team.members[m]
            embed.add_field(
                name=LANE[l],
                value=f"<@{member.discord_id}> ({member.name})",
                inline=False,
            )
        await self.context.send(embed=embed)

    async def send_custom_team(self, team: Team, members: list[Member]):
        embed = Embed(
            title=f"{team.name} 팀",
            description="새로운 대전을 구성했어요.",
            color=0xBEBEFE,
        )
        embed.add_field(
            name="1팀",
            value="\n".join(
                [f"<@{member.discord_id}> ({member.name})" for member in members[:5]]
            ),
            inline=False,
        )
        embed.add_field(
            name="2팀",
            value="\n".join(
                [f"<@{member.discord_id}> ({member.name})" for member in members[5:]]
            ),
            inline=False,
        )
        await self.context.send(embed=embed)


class TeamInfoController(BaseTeamController):
    def __init__(self, context: "Context") -> None:
        super().__init__(context)

    async def get_team_from_view(self, teams: list[Team]) -> Team | None:
        view = TeamInfoSelectView(teams)
        message = await self.context.send(
            "나가려는 팀을 선택해 주세요.", view=view, ephemeral=True
        )
        result = await view.wait()
        if result:
            await message.edit(
                content="팀을 선택하지 않았어요.", view=None, delete_after=5
            )
            return None
        await message.delete()
        return view.selected_team

    async def send_team_info(self, team: Team):
        embed = Embed(
            title=f"**{team.name}** 팀",
            color=Colors.BASE,
        )
        embed.add_field(
            name=f"현재 팀원: {len(team.members)}",
            value="\n".join(
                [f"<@{member.discord_id}> ({member.name})" for member in team.members]
            ),
        )
        await self.context.send(embed=embed, ephemeral=True, silent=True)
