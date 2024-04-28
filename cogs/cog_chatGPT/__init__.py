import logging
from typing import TYPE_CHECKING

from discord import ChannelType
from discord.ext import commands

from utils.logger import get_logger

from . import summarize
from .chatGPT import ChatHandler, CommandHandler, NewChatHandler

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

    @commands.hybrid_command(name="summarize", description="summarize the chat.")
    async def summarize(self, context: "Context", *, time: int = 24) -> None:
        channel = context.channel

        if not summarize.check_time(time):
            await context.send(
                f"{summarize.MAX_DAYS}일 이내로 설정해주세요.", ephemeral=True
            )
            return

        if not summarize.check_channel(channel):
            await context.send(
                "이 명령어는 텍스트 채널에서만 사용할 수 있어요.", ephemeral=True
            )
            return

        new_msg = await context.send("이전 메세지를 불러오고 있어요...", ephemeral=True)
        messages = await summarize.get_channel_messages(channel, time)
        if not messages:
            await context.send(
                f"이전 {time}시간 동안에 메시지가 없어요.", ephemeral=True
            )
            return

        await new_msg.edit(content="요약 중...")
        result = await summarize.get_summary(messages)
        await new_msg.edit(content=result)
        return

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
