from datetime import datetime, timedelta

import discord
from discord import Embed, Guild, TextChannel, app_commands
from discord.ext import commands
from discord.ext.commands import Context

from bot import ServantBot
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class Monitor(commands.Cog, name="monitor"):
    def __init__(self, bot: ServantBot) -> None:
        self.bot = bot

        self._restrict = False

        self.target_id = int(config.monitor.get("id", "0"))
        self.target_name = config.monitor.get("name", "")
        self.channel_id = int(config.monitor.get("channel", "0"))
        self.target_guild: dict[int, dict] = {}

        self._start_time_val = datetime.now()
        self._start_time_lol = datetime.now()

    @commands.hybrid_command(
        name="monitoring",
        description="김시 기능을 켜고 끕니다.",
    )
    @app_commands.choices(
        onoff=[
            app_commands.Choice(name="on", value="on"),
            app_commands.Choice(name="off", value="off"),
        ]
    )
    async def monitoring(self, context: Context, onoff: str) -> None:
        user_id = self.target_id
        if user_id == 0:
            await context.send("몰컴 감시 대상이 설정되지 않았습니다.", ephemeral=True)
            return
        user = context.guild.get_member(user_id)
        if not user:
            await context.send("몰컴 감시 대상을 찾을 수 없습니다.", ephemeral=True)
            return

        if onoff == "on":
            self.target_guild[context.guild.id] = {}
            await context.send(f"{user.mention} 몰컴 감시기 가동", ephemeral=True)
        elif onoff == "off":
            self.target_guild.pop(context.guild.id, None)
            await context.send(f"{user.mention} 몰컴 감시기 중지", ephemeral=True)
        else:
            await context.send("잘못된 입력입니다.")

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        guild = before.guild
        user = guild.get_member(self.target_id)
        channel = self.get_channel(guild, self.channel_id)

        if guild.id in self.target_guild and before.id == user.id:
            data = self.target_guild[guild.id]
            if before.desktop_status != after.desktop_status:
                if after.desktop_status == discord.Status.online:
                    logger.info(f"{self.target_name} 컴퓨터 온라인 검거")
                    data["start_time"] = datetime.now()
                    data["status"] = "online"
                elif after.desktop_status == discord.Status.offline:
                    logger.info(f"{self.target_name} 컴퓨터 오프라인 검거")
                    if data["status"] == "online":
                        data["end_time"] = datetime.now()
                        if data.get("alerted", False):
                            await self.alert_end(channel)

            if before.activity == None or after.activity != None:
                if data["status"] == "online" and not data.get("alerted", False):
                    logger.info(f"{self.target_name} 몰컴 검거")
                    await self.alert_start(channel)
                    data["alerted"] = True

            # save changed data
            self.target_guild[guild.id] = data

    async def alert_start(self, channel: TextChannel):
        await channel.send(
            "WARNING! WARNING! WARNING!\n"
            f"{self.target_name} 몰컴 검거\n"
            "WARNING! WARNING! WARNING!"
        )

    async def alert_end(self, channel: TextChannel, data):
        start_date = data["start_time"].strftime("%m/%d %H:%M")
        end_date = data["end_time"].strftime("%m/%d %H:%M")
        duration = data["end_time"] - data["start_time"]

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
            f"{self.target_name} 몰컴 종료\n"
            f"{start_date} ~ {end_date}\n"
            f"{strfdelta(duration)} 동안 몰컴 완료!\n"
            "WARNING! WARNING! WARNING!"
        )

    def get_channel(self, guild: Guild, channel_id: int):
        channel = guild.get_channel(channel_id) or guild.text_channels[0]
        return channel


async def setup(bot: ServantBot) -> None:
    await bot.add_cog(Monitor(bot))
