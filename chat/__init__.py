import asyncio
import logging
import os
from time import time
from typing import AsyncGenerator

import discord
import openai
from discord.ext.commands import Bot
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall

from database import ChatDataManager

from .function import ToolHandler


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
                elif isinstance(value_a, list) and isinstance(value_b, list):
                    merged_dict[key] = self._merge_list(value_a, value_b)
                elif value_a is None or value_b is None:
                    merged_dict[key] = value_a or value_b
            else:
                merged_dict[key] = dict_b[key]

        return merged_dict

    def _merge_list(self, list_a: list, list_b: list) -> list:
        list_a_index = [value["index"] for value in list_a]
        list_b_index = [value["index"] for value in list_b]
        result = []
        for value_a in list_a:
            for value_b in list_b:
                if value_a["index"] == value_b["index"]:
                    result.append(self._merge_dict(value_a, value_b))

        for value_a in list_a:
            if value_a["index"] not in list_b_index:
                result.append(value_a)

        for value_b in list_b:
            if value_b["index"] not in list_a_index:
                result.append(value_b)
        return result


class ChatHandler:
    def __init__(self, bot: Bot, db: ChatDataManager, message: discord.Message) -> None:
        self.bot = bot
        self.logger: logging.Logger = bot.logger
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db = db
        self.cooldown = 0.5
        self.response_txt = "생각 중..."
        self.old_response_txt = self.response_txt
        self.channel = message.channel
        self.req_message = message
        self.tool_handler = ToolHandler(bot, self.channel)

    async def chat_response(self):
        self.append_content(self.channel.id, "user", self.req_message.content)
        self.res_message = await self.channel.send(self.response_txt)
        while True:
            res = None
            now = time()
            async for response in self.get_response():
                res = response if res is None else res + response
                self.response_txt = self.get_content(res)
                if (
                    time() - now > self.cooldown
                    and self.old_response_txt != self.response_txt
                ):
                    now = time()
                    await self.edit_message()
            await asyncio.sleep(self.cooldown - (time() - now))
            await self.edit_message()
            self.logger.info(f"chat response: {res.model_dump_json()}")

            if res.choices[0].finish_reason == "stop":
                self.append_content(
                    self.channel.id, "assistant", res.choices[0].delta.content
                )
                break
            elif res.choices[0].finish_reason == "tool_calls":
                self.append_tool_calls(
                    self.channel.id, res.choices[0].delta.model_dump()["tool_calls"]
                )
                await self.handle_tool_calls(res.choices[0].delta.tool_calls)

    async def get_response(self) -> AsyncGenerator[ChatResponse, None]:
        messages = self.get_messages(self.channel.id)
        self.logger.info(messages)
        completion = await self.client.chat.completions.create(
            messages=messages,
            model="gpt-4-1106-preview",
            tools=self.tool_handler.get_tools(),
            stream=True,
        )
        async for event in completion:
            yield ChatResponse(event.model_dump())

    def get_content(self, res: ChatResponse) -> str:
        res_content = ""
        if res.choices[0].delta.content:
            res_content = res.choices[0].delta.content
        elif res.choices[0].delta.tool_calls:
            for tool_call in res.choices[0].delta.tool_calls:
                res_content += f"{tool_call.function.name} 호출됨\n"
        return res_content

    async def edit_message(self) -> None:
        if self.response_txt:
            self.old_response_txt = self.response_txt
            await self.res_message.edit(content=self.response_txt)

    def get_messages(self, thread_id: int) -> list[dict]:
        messages = []
        thread = self.db.get_thread(thread_id)
        system_message = thread["system"]
        if system_message:
            messages += self.message_line("system", system_message)
        messages += thread["messages"]
        return messages

    def append_content(self, thread_id: int, role: str, content: str = None) -> None:
        self.role_check(role)
        self.db.append_message(thread_id, {"role": role, "content": content})

    def append_tool_calls(self, thread_id: int, tool_calls: list[dict]) -> None:
        self.db.append_message(
            thread_id, {"role": "assistant", "tool_calls": tool_calls}
        )

    def append_tool_message(
        self, thread_id: int, tool_call_id: str, content: str
    ) -> None:
        self.db.append_message(
            thread_id,
            {"role": "tool", "content": content, "tool_call_id": tool_call_id},
        )

    async def handle_tool_calls(self, tool_calls: list[ChoiceDeltaToolCall]) -> None:
        for tool_call in tool_calls:
            if tool_call.type == "function":
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments
                response = await self.tool_handler.process(function_name, function_args)
                self.append_tool_message(self.channel.id, tool_call.id, response)

    def message_line(self, role: str, content: str) -> dict:
        self.role_check(role)
        return {"role": role, "content": content}

    def role_check(self, role: str) -> None:
        if role not in ["system", "user", "assistant", "tool"]:
            raise ValueError(
                "role must be one of 'system', 'user', 'assistant', 'tool'"
            )
