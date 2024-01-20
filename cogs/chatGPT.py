import logging
import os
from time import time

import discord
import openai
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

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
