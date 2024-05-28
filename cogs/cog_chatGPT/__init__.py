from typing import TYPE_CHECKING

from discord import ChannelType
from discord.ext import commands

from database.chat import get_thread_info
from utils.hash import generate_key
from utils.logger import get_logger

from .handler import ChatHandler, CommandHandler, NewChatHandler, SummarizeHandler

if TYPE_CHECKING:
    from discord import Message
    from discord.ext.commands import Context

    from bot import ServantBot


class ChatGPT(commands.Cog, name="chatGPT"):
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot
        self.logger = get_logger("chatGPT")

    @commands.hybrid_command(name="chat", description="start a new chat with chatGPT.")
    async def chat(self, context: "Context") -> None:
        handler = NewChatHandler(self.bot, context)
        await handler.run()

    @commands.hybrid_command(name="view", description="test")
    async def view(self, context: "Context") -> None:
        guild_name = context.guild.name
        key = generate_key(str(context.channel.id), 6)
        i = await get_thread_info(
            guild_name,
            key,
        )
        print(i)
        await context.send(content=f"{i['goals']}")

    @commands.hybrid_command(name="summarize", description="summarize the chat.")
    async def summarize(self, context: "Context", *, time: int = 1) -> None:
        handler = SummarizeHandler(self.bot, context, time)
        await handler.run()

    @commands.Cog.listener()
    async def on_message(self, message: "Message") -> None:
        if message.author.bot:
            return

        if (
            message.channel.type == ChannelType.public_thread
            and message.channel.owner == self.bot.user
        ):
            if message.content.startswith("?"):
                handler = CommandHandler(self.bot, message)
            else:
                handler = ChatHandler(self.bot, message)
            await handler.run()


async def setup(bot: "ServantBot") -> None:
    await bot.add_cog(ChatGPT(bot))
