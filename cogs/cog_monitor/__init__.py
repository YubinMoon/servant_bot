import os
import platform
from datetime import datetime
from time import time

import discord
from discord import Guild, app_commands
from discord.ext import commands
from discord.ext.commands import Context
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts.chat import BaseChatPromptTemplate

from bot import ServantBot
from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class Monitor(commands.Cog, name="monitor"):
    def __init__(self, bot: ServantBot) -> None:
        self.bot = bot

        self._restrict = False
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
        user_id = int(config.monitor.get("id", "0"))
        if user_id == 0:
            await context.send("몰컴 감시 대상이 설정되지 않았습니다.", ephemeral=True)
        user = context.guild.get_member(user_id)
        if not user:
            await context.send("몰컴 감시 대상을 찾을 수 없습니다.", ephemeral=True)

        if onoff == "on":
            self._restrict = True
            await context.send(f"{user.mention} 몰컴 감시기 가동", ephemeral=True)
        elif onoff == "off":
            self._restrict = False
            await context.send(f"{user.mention} 몰컴 감시기 중지", ephemeral=True)
        else:
            await context.send("잘못된 입력입니다.")

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        user_id = int(config.monitor.get("id", "0"))
        channel_id = int(config.monitor.get("channel", "0"))
        guild_id = int(config.monitor.get("guild", "0"))

        guild = before.guild
        user = guild.get_member(user_id)
        channel = self.get_channel(guild, channel_id)
        first_channel = guild.text_channels[0]
        test_channel = guild.text_channels[-1]

        if guild.id == int(os.getenv("PJY_GUILD_ID")):
            logger.info(f"user: {after.display_name}")
            logger.info(f"{before.activity} -> {after.activity}")
            if after.id == int(os.getenv("PJY_ID")):
                logger.info("타켓 확인")
                if (
                    before.desktop_status != after.desktop_status
                    and after.desktop_status == discord.Status.online
                ):
                    logger.info(f"{os.getenv('PJY_NAME')} 컴퓨터 온라인 검거")
                    if self._restrict:
                        await test_channel.send(
                            f"{os.getenv('PJY_NAME')} 컴퓨터 온라인 검거.", silent=True
                        )

                before_activity = (
                    "" if before.activity is None else (before.activity.name or "")
                )
                after_activity = (
                    "" if after.activity is None else (after.activity.name or "")
                )
                if before_activity != after_activity:
                    if "VALORANT" in after_activity:
                        if after.voice is None:
                            logger.info(f"{os.getenv('PJY_NAME')} 몰로란트 시작")
                            if self._restrict:
                                self._start_time_val = datetime.now()
                                await first_channel.send(
                                    "WARNING! WARNING! WARNING!\n"
                                    f"{after.mention}몰로란트 검거\n"
                                    "WARNING! WARNING! WARNING!"
                                )
                    elif "League of Legends" in after_activity:
                        if after.voice is None:
                            logger.info(f"{os.getenv('PJY_NAME')} 몰롤 시작")
                            if self._restrict:
                                self._start_time_lol = datetime.now()
                                await first_channel.send(
                                    "WARNING! WARNING! WARNING!\n"
                                    f"{after.mention}몰롤 검거\n"
                                    "WARNING! WARNING! WARNING!"
                                )
                    elif "VALORANT" in before_activity and after_activity == "":
                        if after.voice is None:
                            logger.info(f"{os.getenv('PJY_NAME')} 게임 종료")
                            if self._restrict:
                                _time = datetime.now() - self._start_time_val
                                seconds = _time.seconds
                                minute = seconds // 60
                                time_format = "몰컴 시간: "
                                if minute:
                                    time_format += f"{minute}분 "
                                time_format += f"{seconds % 60}초"

                                await first_channel.send(
                                    "WARNING! WARNING! WARNING!\n"
                                    f"{after.mention}몰로란트 종료\n"
                                    f"{time_format}\n"
                                    "WARNING! WARNING! WARNING!"
                                )
                    elif (
                        "League of Legends" in before_activity and after_activity == ""
                    ):
                        if after.voice is None:
                            logger.info(f"{os.getenv('PJY_NAME')} 게임 종료")
                            if self._restrict:
                                _time = datetime.now() - self._start_time_lol
                                seconds = _time.seconds
                                minute = seconds // 60
                                time_format = "몰컴 시간: "
                                if minute:
                                    time_format += f"{minute}분 "
                                time_format += f"{seconds % 60}초"

                                await first_channel.send(
                                    "WARNING! WARNING! WARNING!\n"
                                    f"{after.mention}몰롤 종료\n"
                                    f"{time_format}\n"
                                    "WARNING! WARNING! WARNING!"
                                )

    def get_channel(self, guild: Guild, channel_id: int):
        channel = guild.get_channel(channel_id) or guild.text_channels[0]
        return channel


async def setup(bot: ServantBot) -> None:
    await bot.add_cog(Monitor(bot))
