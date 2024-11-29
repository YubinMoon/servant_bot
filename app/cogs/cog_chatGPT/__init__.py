from typing import TYPE_CHECKING

from discord import ChannelType
from discord.ext import commands

from ...common.logger import get_logger
from .handler import ChatHandler, NewChatHandler

if TYPE_CHECKING:
    from bot import ServantBot
    from discord import Message
    from discord.ext.commands import Context


class ChatGPT(commands.Cog, name="chatGPT"):
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot
        self.logger = get_logger("chatGPT")

    @commands.hybrid_command(name="chat", description="start a new chat with chatGPT.")
    async def chat(self, context: "Context") -> None:
        handler = NewChatHandler(self.bot, context)
        await handler.run()

    @commands.Cog.listener()
    async def on_message(self, message: "Message") -> None:
        if message.author.bot:
            return

        if (
            message.channel.type == ChannelType.public_thread
            and message.channel.owner == self.bot.user
        ):
            handler = ChatHandler(self.bot, message)
            await handler.run()


async def setup(bot: "ServantBot") -> None:
    await bot.add_cog(ChatGPT(bot))
