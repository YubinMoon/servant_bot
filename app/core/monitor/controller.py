from datetime import timedelta
from typing import TYPE_CHECKING

from ..model.monitor import Target, TargetState

if TYPE_CHECKING:
    from discord import Guild
    from discord.abc import MessageableChannel


def get_channel(guild: "Guild", channel_id: int):
    channel = guild.get_channel(channel_id) or guild.text_channels[0]
    return channel


async def alert_start(channel: "MessageableChannel", target: Target):
    await channel.send(
        "WARNING! WARNING! WARNING!\n"
        f"{target.name} 몰컴 검거\n"
        "WARNING! WARNING! WARNING!"
    )


async def alert_end(channel: "MessageableChannel", target: Target, state: TargetState):
    start_date = state.start_time.strftime("%m/%d %H:%M")
    end_date = state.end_time.strftime("%m/%d %H:%M")
    duration = state.end_time - state.start_time

    def strfdelta(tdelta: timedelta):
        hour = tdelta.seconds // 3600
        minute = (tdelta.seconds % 3600) // 60
        result = ""
        if hour:
            result += f"{hour}시간"
        if minute:
            result += f" {minute}분"
        return result

    await channel.send(
        "WARNING! WARNING! WARNING!\n"
        f"{target.name} 몰컴 종료\n"
        f"{start_date} ~ {end_date}\n"
        f"{strfdelta(duration)} 동안 몰컴 완료!\n"
        "WARNING! WARNING! WARNING!"
    )
