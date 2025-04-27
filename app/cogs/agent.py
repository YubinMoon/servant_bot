import logging
from typing import TYPE_CHECKING

from agents import ItemHelpers
from discord import ChannelType, app_commands
from discord.ext import commands

from app.common.utils.text_splitter import split_into_chunks
from app.core.agent import Messenger, controller, handler

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
        messenger = Messenger(
            thread=channel,
            splitter=split_into_chunks,
        )
        messenger.add_content("생각 중...")
        await messenger.update_message()
        messages = await controller.parse_message(message)
        contents = [message.to_content() for message in messages]
        pre_messages = handler.get_message(channel.id) + [
            {
                "role": "user",
                "content": contents,
            }
        ]
        result = handler.call_agent(
            thread_id=channel.id,
            user_id=message.author.id,
            messages=pre_messages,
        )
        messenger.del_content()
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                continue
            elif event.type == "agent_updated_stream_event":
                continue
            elif event.type == "run_item_stream_event":
                if event.item.type == "message_output_item":
                    messenger.add_content(ItemHelpers.text_message_output(event.item))
                elif event.item.type == "tool_call_item":
                    messenger.add_content(event.item.raw_item.name, "tool")
                await messenger.update_message()
        handler.save_message(channel.id, result.to_input_list())

    @commands.Cog.listener()
    async def on_command_error(self, context: "Context", error) -> None:
        if isinstance(error, commands.errors.CommandError):
            logger.error(f"{context.author} (ID: {context.author.id}) raised {error}")
