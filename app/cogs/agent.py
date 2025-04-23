import logging
import traceback
from typing import TYPE_CHECKING

from discord import ChannelType, app_commands
from discord.ext import commands

from app.core.agent import controller, handler

if TYPE_CHECKING:
    from discord import Message
    from discord.ext.commands import Context

    from app.bot import ServantBot

logger = logging.getLogger(__name__)


class Agent(commands.Cog, name="agent"):
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot

    @commands.hybrid_group(name="agent")
    async def agent(self, context: "Context") -> None:
        pass

    @agent.command(name="new", description="새로운 채팅 시작")
    @app_commands.describe(goal="채팅 설명")
    async def new(self, context: "Context", *, goal: str = "") -> None:
        result = await handler.gen_thread_info(
            thread_id=context.channel.id,
            user_id=context.author.id,
            message=goal,
        )
        await controller.setup_new_chat(context, result.title, result.nofication)
        logger.info(f"created new chat: {context.author.name}")

    @commands.Cog.listener()
    async def on_message(self, message: "Message"):
        channel = message.channel
        if (
            channel.type != ChannelType.public_thread
            or channel.owner != self.bot.user
            or message.author == self.bot.user
        ):
            return
        logger.debug(f"message from {message.author.name}: {message.content}")
        thread_id = channel.id
        user_id = message.author.id
        messages = await controller.parse_message(message)
        result = await handler.call_agent(
            thread_id=thread_id,
            user_id=user_id,
            messages=messages,
        )
        logger.debug(f"result: {result}")
        await controller.send_message(thread=channel, content=result)

    @commands.Cog.listener()
    async def on_command_error(self, context: "Context", error) -> None:
        if isinstance(error, commands.errors.CommandError):
            logger.error(f"{context.author} (ID: {context.author.id}) raised {error}")
