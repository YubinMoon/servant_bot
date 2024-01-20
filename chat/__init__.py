import os
import openai
import logging
import discord
import asyncio
from time import time
from datetime import datetime
from discord.ext.commands import Bot, Context

from dotenv import load_dotenv
from database import ChatDataManager
from openai.types.chat import ChatCompletionChunk
from typing import AsyncGenerator


class ChatResponse(ChatCompletionChunk):
    def __init__(self, data) -> None:
        super().__init__(**data)

    def __add__(self, other: "ChatResponse") -> "ChatResponse":
        if self.id != other.id:
            raise ValueError("cannot add different response")
        new = self.model_dump()
        new["choices"][0] = self._merge_dict(
            self.choices[0].model_dump(), other.choices[0].model_dump()
        )
        return ChatResponse(new)

    def _merge_dict(self, dict_a: dict, dict_b: dict) -> dict:
        merged_dict = dict(dict_a)

        for key in dict_b:
            if key in dict_a:
                value_a = dict_a[key]
                value_b = dict_b[key]
                if isinstance(value_a, dict) and isinstance(value_b, dict):
                    merged_dict[key] = self._merge_dict(value_a, value_b)
                elif isinstance(value_a, str) and isinstance(value_b, str):
                    merged_dict[key] = value_a + value_b
                elif value_a is None or value_b is None:
                    merged_dict[key] = value_a or value_b
            else:
                # dict_b에만 있는 키라면 추가
                merged_dict[key] = dict_b[key]

        return merged_dict


class ChatHandler:
    def __init__(self, bot: Bot, db: ChatDataManager) -> None:
        self.bot = bot
        self.logger: logging.Logger = bot.logger
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db = db
        self.cooldown = 0.5
        self.old_response_txt = ""
        self.response_txt = "생각 중..."
        self.message: discord.Message = None

    async def chat_response(self, message: discord.Message):
        self.set_message(message.channel.id, "user", message.content)
        self.message = await message.channel.send(self.response_txt)
        while True:
            res = None
            now = time()
            async for response in self.get_response(message):
                res = response if res is None else res + response
                content = res.choices[0].delta.content
                if time() - now > self.cooldown and content:
                    await self.message.edit(content=content)
                    now = time()
            await asyncio.sleep(self.cooldown - (time() - now))
            self.logger.info(f"chat response: {res.model_dump_json()}")
            await self.message.edit(content=res.choices[0].delta.content)
            if res.choices[0].finish_reason == "stop":
                self.set_message(
                    message.channel.id, "assistant", res.choices[0].delta.content
                )
                break

    async def get_response(
        self, message: discord.Message
    ) -> AsyncGenerator[ChatResponse, None]:
        messages = self.get_messages(message.channel.id)
        print(messages)
        completion = await self.client.chat.completions.create(
            messages=messages,
            model="gpt-4-1106-preview",
            stream=True,
        )
        async for event in completion:
            yield ChatResponse(event.model_dump())

    def get_messages(self, thread_id: int) -> list[dict]:
        messages = []
        thread = self.db.get_thread(thread_id)
        system_message = thread["system"]
        if system_message:
            messages += self.message_line("system", system_message)
        messages += thread["messages"]
        return messages

    def set_message(self, thread_id: int, role: str, content: str) -> None:
        if role not in ["system", "user", "assistant", "tool"]:
            raise ValueError(
                "role must be one of 'system', 'user', 'assistant', 'tool'"
            )
        self.db.append_message(thread_id, {"role": role, "content": content})

    def message_line(self, role: str, content: str) -> dict:
        if role not in ["system", "user", "assistant", "tool"]:
            raise ValueError(
                "role must be one of 'system', 'user', 'assistant', 'tool'"
            )
        return {"role": role, "content": content}
