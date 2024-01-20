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
            handler = ChatHandler(self.bot, self.db)
            await handler.chat_response(message)
            return

    # async def handle_chat(self, message: discord.Message) -> None:
    #     time_now = time()
    #     messages = self.get_messages_from_thread(message.channel)
    #     completion = await client.chat.completions.create(
    #         messages=messages,
    #         model="gpt-4-1106-preview",
    #         stream=True,
    #     )
    #     answer = await message.channel.send("생각중...")
    #     answer_text = ""
    #     async for event in completion:
    #         if event.choices[0].finish_reason == "stop":
    #             break
    #         answer_text += event.choices[0].delta.content
    #         if time() - time_now > 0.8 and answer_text:
    #             time_now = time()
    #             await answer.edit(content=answer_text)
    #     await answer.edit(content=answer_text)

    # async def get_messages_from_thread(self, thread: discord.Thread) -> list[dict]:
    #     messages = []
    #     async for msg in thread.history(limit=20, oldest_first=True):
    #         if msg.type == discord.MessageType.thread_starter_message:
    #             continue
    #         messages.append(
    #             {
    #                 "role": "assistant" if msg.author.bot else "user",
    #                 "content": msg.content,
    #             }
    #         )
    #     return messages


async def setup(bot) -> None:
    await bot.add_cog(ChatGPT(bot))
