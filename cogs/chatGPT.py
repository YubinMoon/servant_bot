import logging
from time import time

import discord
from discord.ext import commands
from discord.ext.commands import Context

import summarize
from chat import ChatHandler
from database import ChatDataManager


class ChatGPT(commands.Cog, name="chatGPT"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = ChatDataManager(bot)
        self.logger: logging.Logger = bot.logger

    @commands.hybrid_command(name="chat", description="start a new chat with chatGPT.")
    async def chat(self, context: Context) -> None:
        new_msg = await context.send("새 쓰래드를 시작할게요.")
        thread = await new_msg.create_thread(
            name="chat with GPT", auto_archive_duration=60, reason="new chat"
        )
        self.db.set_thread(thread.id)
        self.logger.info(f"new chat thread created by {context.author.name}")

    @commands.hybrid_command(name="summarize", description="summarize the chat.")
    async def summarize(self, context: Context, *, time: int = 24) -> None:
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
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.channel.type == discord.ChannelType.public_thread:
            handler = ChatHandler(self.bot, self.db, message)
            await handler.chat_response()
            return


async def setup(bot) -> None:
    await bot.add_cog(ChatGPT(bot))
