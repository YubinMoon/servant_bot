from datetime import timedelta, timezone
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from discord.ext.commands import Context

from app.core.monitor import controller

from ..common.logger import get_logger
from ..core.database import get_session
from ..core.monitor import handler

if TYPE_CHECKING:
    from ..bot import ServantBot

logger = get_logger(__name__)

UTC_9 = timezone(timedelta(hours=9))


class Monitor(commands.Cog, name="monitor"):
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot

    @commands.guild_only()
    @commands.hybrid_group(name="monitor")
    async def monitor(self, context: "Context") -> None:
        pass

    @commands.guild_only()
    @monitor.command(name="set", description="몰컴 감시 대상 설정")
    async def set(
        self,
        context: "Context",
        user: discord.Member,
        name: str,
        channel: discord.TextChannel,
    ) -> None:
        with get_session() as session:
            handler.set_target(
                session,
                user.id,
                name,
                context.guild.id,
                channel.id,
            )
            await context.send(
                f"{user.mention} 몰컴 감시 대상으로 설정되었습니다.", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        with get_session() as session:
            target = handler.get_targets(
                session,
                before.id,
                before.guild.id,
            )
            if not target:
                return

            if before.desktop_status != after.desktop_status:
                if after.desktop_status == discord.Status.online:
                    logger.info(f"{target.name} 컴퓨터 온라인 검거")
                    handler.arrest_online(session, target)
                elif after.desktop_status == discord.Status.offline:
                    logger.info(f"{target.name} 컴퓨터 오프라인 검거")
                    state = handler.arrest_offline(session, target)
                    if state and state.alerted:
                        channel = controller.get_channel(after.guild, target.channel_id)
                        await controller.alert_end(channel, target, state)

            if before.activity == None and after.activity != None:
                state = handler.get_open_state(session, target)
                if state and state.alerted == False:
                    logger.info(f"{target.name} 몰컴 검거")
                    channel = controller.get_channel(after.guild, target.channel_id)
                    await controller.alert_start(channel, target)
                    handler.set_alerted(session, state)
