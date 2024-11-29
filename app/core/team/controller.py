from datetime import datetime
from typing import TYPE_CHECKING

from discord import Embed, NotFound, ui

from ...common.utils.color import Colors
from ..error.team import TeamError
from ..model.team import Member, Team

if TYPE_CHECKING:
    from discord import Message
    from discord.abc import MessageableChannel
    from discord.ext.commands import Context

TEAM_1_NAME = "팀 1"
TEAM_2_NAME = "팀 2"


async def fetch_message(channel: "MessageableChannel", team: Team) -> "Message":
    message_id = team.message_id
    not_found_error = TeamError(
        "Team Create message is not found.",
        "팀을 찾을 수 없어요.",
        "**/q**로 팀을 새로 생성해 보세요.",
        alert=False,
    )
    try:
        message = await channel.fetch_message(message_id)
    except NotFound as e:
        raise not_found_error
    if message.embeds == []:
        raise not_found_error
    return message


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


async def send_join_alert(
    message: "Message",
    team: Team,
    user_id: int,
):
    embed = Embed(
        description=f"<@{user_id}>님이 **{team.name}**팀에 참가했어요.",
        color=Colors.BASE,
    )
    await message.reply(embed=embed)


async def send_left_alert(
    message: "Message",
    team: Team,
    user_id: int,
):
    embed = Embed(
        description=f"<@{user_id}>님이 **{team.name}**팀에서 나갔어요.",
        color=Colors.BASE,
    )
    await message.reply(embed=embed)


async def update_team_message(
    message: "Message",
    team: Team,
    view=ui.View,
):
    members = team.members
    embed = message.embeds[0]
    embed.set_field_at(
        index=0,
        name=f"현제 인원: {len(members)}",
        value=" - ".join([f"<@{member.discord_id}>" for member in members]),
    )
    await message.edit(embed=embed, view=view)


async def show_team_list(
    context: "Context",
    teams: list[Team],
    view: ui.View,
):
    description = str()
    for idx, team in enumerate(teams):
        tdelta = datetime.now() - team.created_at
        minute = tdelta.seconds // 60
        hour = tdelta.seconds // 3600
        time = f"{hour}시간 {minute}분" if hour > 0 else f"{minute}분"
        description += f"### {idx+1}. {team.name} ({len(team.members)}명)\n"
        description += f"**{time} 전**에 생성됨\n"
    embed = Embed(
        title="팀 목록",
        description=description,
        color=Colors.BASE,
    )
    embed.set_footer(text="팀을 선택해 주세요.")
    message = await context.send(embed=embed, view=view, ephemeral=True)
    await view.wait()
    await message.delete()


async def show_team_detail(
    message: "Message",
    team: Team,
):
    members = team.members
    embed = Embed(
        title=f"**{team.name}** 팀",
        color=Colors.BASE,
    )
    embed.add_field(
        name=f"현재 팀원: {len(members)}",
        value="\n".join(
            [f"<@{member.discord_id}> ({member.name})" for member in members]
        ),
    )
    await message.reply(embed=embed)


async def send_rank_team(message: "Message", team: Team, rank_team: list[int]) -> None:
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
    await message.reply(embed=embed)


async def send_custom_team(message: "Message", team: Team, rank_team: list[int]):
    embed = Embed(
        title=f"{team.name} 팀",
        description="새로운 대전을 구성했어요.",
        color=0xBEBEFE,
    )
    team_group: dict[str, list[Member]] = {TEAM_1_NAME: [], TEAM_2_NAME: []}
    for idx, m_idx in enumerate(rank_team):
        member = team.members[m_idx]
        team_name = TEAM_1_NAME if idx < ((len(rank_team) + 1) // 2) else TEAM_2_NAME
        team_group[team_name].append(member)
    for key, values in team_group.items():
        embed.add_field(
            name=key,
            value="\n".join(
                [f"<@{member.discord_id}> ({member.name})" for member in values]
            ),
            inline=False,
        )
    await message.reply(embed=embed)


async def send_delete_alert(message: "Message", team: Team):
    embed = Embed(
        description=f"**{team.name}** 팀이 삭제되었어요.",
        color=Colors.DANGER,
    )
    await message.reply(embed=embed)
