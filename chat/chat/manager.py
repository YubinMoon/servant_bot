import asyncio
import os
from time import time
from typing import TYPE_CHECKING, AsyncGenerator

import openai
from discord import Embed, HTTPException

from database import ChatDataManager
from utils import color
from utils.hash import generate_key
from utils.logger import get_logger

from ..error import ChatResponseError, ContentFilterError
from .function import ToolHandler
from .model import ChatResponse

if TYPE_CHECKING:
    from discord.abc import MessageableChannel
    from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall

    from bot import ServantBot


class ChatManager:
    role_list = ["system", "user", "assistant", "tool"]
    base_response_txt = "생각 중..."
    cooldown = 1

    def __init__(self, bot: "ServantBot", channel: "MessageableChannel") -> None:
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.bot = bot
        self.db = ChatDataManager(bot)
        self.channel = channel
        self.guild = channel.guild
        self.logger = get_logger("chat_manager")
        self.tool_handler = ToolHandler(bot, channel)
        self.key: str = generate_key(str(channel.id), 6)

        self.response_txt = self.base_response_txt
        self.old_response_txt = self.response_txt

    async def run_task(self) -> None:
        self.res_chat_message = await self.channel.send(self.base_response_txt)

        while True:
            res = await self._chat_response()
            if res is None:
                return
            res_content = res.choices[0].delta.content
            res_finish_reason = res.choices[0].finish_reason

            if res_content is not None:
                self._append_assistant_message(res_content)
                if res_finish_reason == "tool_calls":
                    await self.res_chat_message.add_reaction("✅")
                    res_content = ""
                    for tool_call in res.choices[0].delta.tool_calls:
                        res_content += f"{tool_call.function.name} 호출 중...\n"
                    self.res_chat_message = await self.channel.send(res_content)

            if res_finish_reason == "stop":
                await self.res_chat_message.add_reaction("✅")
                break
            elif res_finish_reason == "tool_calls":
                self._append_tool_calls(res.choices[0].delta.model_dump()["tool_calls"])
                await self._handle_tool_calls(res.choices[0].delta.tool_calls)
                await self.res_chat_message.add_reaction("✅")
                self.res_chat_message = await self.channel.send(self.base_response_txt)
            elif res_finish_reason == "length":
                self.res_chat_message = await self.channel.send(self.base_response_txt)
                self.logger.warning("response finished because of length")
            elif res_finish_reason == "content_filter":
                await self.res_chat_message.delete()
                self.logger.error("response finished because of content filter")
                raise ContentFilterError("response finished because of content filter")
            else:
                self.logger.error(f"finish_reason: {res.choices[0].finish_reason}")

    async def _chat_response(self) -> "ChatResponse":
        res: ChatResponse = None
        now: float = time()
        try:
            async for response in self._get_response_stream():
                res = response if res is None else res + response
                self.response_txt = self._parse_content(res)
                if (
                    time() - now > self.cooldown
                    and self.old_response_txt != self.response_txt
                ):
                    await self._edit_message()
                    now = time()
            await asyncio.sleep(self.cooldown - (time() - now))
            await self._edit_message()
            self.logger.debug(f"chat response: {res.model_dump_json()}")
        except openai.APIError as e:
            await self.res_chat_message.delete()
            raise ChatResponseError(e.message)
        except HTTPException as e:
            await self.logger.warn("discord length max error")
        return res

    async def _get_response_stream(self) -> AsyncGenerator[ChatResponse, None]:
        messages = self.get_messages()
        completion = await self.client.chat.completions.create(
            messages=messages,
            model="gpt-4-0125-preview",
            tools=self.tool_handler.get_tools(),
            stream=True,
        )
        async for event in completion:
            yield ChatResponse(event.model_dump())

    async def _edit_message(self) -> None:
        if self.response_txt:
            self.old_response_txt = self.response_txt
            await self.res_chat_message.edit(content=self.response_txt)

    def _parse_content(self, res: ChatResponse) -> str:
        res_content = ""
        if res.choices[0].delta.content:
            res_content = res.choices[0].delta.content
        elif res.choices[0].delta.tool_calls:
            for tool_call in res.choices[0].delta.tool_calls:
                res_content += f"{tool_call.function.name} 호출 중...\n"
        return res_content

    async def _handle_tool_calls(self, tool_calls: "list[ChoiceDeltaToolCall]") -> None:
        embed = Embed(title="기능 호출", color=color.BASE)
        for tool_call in tool_calls:
            if tool_call.type == "function":
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments
                response = await self.tool_handler.process(function_name, function_args)
                self._append_tool_message(tool_call.id, response)
                name, value = await self.tool_handler.get_display(function_name)
                embed.add_field(name=name, value=value, inline=True)
        await self.res_chat_message.edit(content="", embed=embed)

    def get_messages(self) -> list[dict]:
        messages = []
        system_message = self.db.get_system_message(self.guild.name, self.key)
        if system_message:
            messages += {"role": "system", "content": system_message}
        raw_messages = self.db.get_messages(self.guild.name, self.key)
        for message in raw_messages:
            messages.append(message["message"])
        return messages

    def append_user_message(self, content: str, message_id: int) -> None:
        data = {
            "message_id": message_id,
            "message": {
                "role": "user",
                "content": content,
            },
        }
        self._append_message(data)

    def _append_assistant_message(self, content: str) -> None:
        data = {
            "message_id": self.res_chat_message.id,
            "message": {
                "role": "assistant",
                "content": content,
            },
        }
        self._append_message(data)

    def _append_tool_calls(self, tool_calls: list[dict]) -> None:
        data = {
            "message_id": self.res_chat_message.id,
            "message": {
                "role": "assistant",
                "tool_calls": tool_calls,
            },
        }
        self._append_message(data)

    def _append_tool_message(self, tool_call_id: str, content: str) -> None:
        data = {
            "message_id": self.res_chat_message.id,
            "message": {
                "role": "tool",
                "content": content,
                "tool_call_id": tool_call_id,
            },
        }
        self._append_message(data)

    def _append_message(self, data: dict) -> None:
        role = data["message"]["role"]
        self.role_check(role)
        self.db.append_message(self.guild.name, self.key, data)

    def role_check(self, role: str) -> None:
        if role not in self.role_list:
            raise ValueError(f"role must be one of {self.role_list}")
