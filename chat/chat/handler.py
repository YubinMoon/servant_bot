import asyncio
import os
from time import time
from typing import TYPE_CHECKING, AsyncGenerator

import openai
from discord import Embed, HTTPException
from openai import APIError

from utils import color

from ..base import BaseMessageHandler
from ..error import ChatResponseError, ContentFilterError
from .function import ToolHandler
from .model import ChatResponse

if TYPE_CHECKING:
    from discord import Message
    from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall

    from bot import ServantBot


class ChatHandler(BaseMessageHandler):
    logger_name = "chat_handler"
    role_list = ["system", "user", "assistant", "tool"]
    base_response_txt = "생각 중..."

    def __init__(self, bot: "ServantBot", message: "Message") -> None:
        super().__init__(bot, message)
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.cooldown = 1.5
        self.response_txt = self.base_response_txt
        self.old_response_txt = self.response_txt
        self.tool_handler = ToolHandler(bot, self.thread)

    async def action(self):
        if await self.is_lock():
            return
        try:
            self.db.lock(self.guild.name, self.key)
            await self.handle_file()
            await self.handle_content()
        except Exception as e:
            raise e
        finally:
            self.db.unlock(self.guild.name, self.key)

    async def is_lock(self) -> bool:
        if self.db.has_lock(self.guild.name, self.key):
            embed = Embed(
                title="아직 답변이 완료되지 않았어요.",
                description="10초 뒤에 질문이 삭제됩니다.",
            )
            reply_msg = await self.message.reply(embed=embed)
            await asyncio.sleep(10)
            await reply_msg.delete()
            await self.message.delete()
            return True
        return False

    async def handle_file(self) -> None:
        files = self.message.attachments
        for file in files:
            if file.filename.endswith(".txt"):
                content = await file.read()
                self.append_user_message(content.decode("utf-8"))
                embed = Embed(
                    title="'txt' 파일 업로드 완료",
                    description="채팅 질문과 함께 입력돼요.",
                )
                await self.message.reply(embed=embed)

    async def handle_content(self) -> None:
        content = self.message.content
        if content == "":
            return
        self.append_user_message(self.message.content)
        self.res_message = await self.thread.send(self.response_txt)
        while True:
            res = await self.chat_response()
            if res is None:
                return
            res_content = res.choices[0].delta.content
            res_finish_reason = res.choices[0].finish_reason

            if res_content is not None:
                self.append_assistant_message(res.choices[0].delta.content)
                if res_finish_reason == ["tool_calls", "length"]:
                    self.res_message = await self.thread.send(self.base_response_txt)

            if res_finish_reason == "stop":
                break
            elif res_finish_reason == "tool_calls":
                self.append_tool_calls(res.choices[0].delta.model_dump()["tool_calls"])
                await self.handle_tool_calls(res.choices[0].delta.tool_calls)
                self.res_message = await self.thread.send(self.base_response_txt)
            elif res_finish_reason == "length":
                self.logger.warning("response finished because of length")
            elif res_finish_reason == "content_filter":
                await self.res_message.delete()
                self.logger.error("response finished because of content filter")
                raise ContentFilterError("response finished because of content filter")
            else:
                self.logger.warning(f"finish_reason: {res.choices[0].finish_reason}")

    async def chat_response(self) -> "ChatResponse":
        res: ChatResponse = None
        now: float = time()
        try:
            async for response in self.get_response():
                res = response if res is None else res + response
                self.response_txt = self.get_content(res)
                if (
                    time() - now > self.cooldown
                    and self.old_response_txt != self.response_txt
                ):
                    await self.edit_message()
                    now = time()
            await asyncio.sleep(self.cooldown - (time() - now))
            await self.edit_message()
            await self.res_message.add_reaction("✅")
            self.logger.debug(f"chat response: {res.model_dump_json()}")
        except APIError as e:
            await self.res_message.delete()
            raise ChatResponseError(e.message)
        except HTTPException as e:
            await self.logger.warn("discord length max error")
        return res

    async def get_response(self) -> AsyncGenerator[ChatResponse, None]:
        messages = self.get_messages()
        completion = await self.client.chat.completions.create(
            messages=messages,
            model="gpt-4-0125-preview",
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
                res_content += f"{tool_call.function.name} 호출 중...\n"
        return res_content

    async def edit_message(self) -> None:
        if self.response_txt:
            self.old_response_txt = self.response_txt
            await self.res_message.edit(content=self.response_txt)

    def get_messages(self) -> list[dict]:
        messages = []
        system_message = self.db.get_system_message(self.guild.name, self.key)
        if system_message:
            messages += {"role": "system", "content": system_message}
        raw_messages = self.db.get_messages(self.guild.name, self.key)
        for message in raw_messages:
            messages.append(message["message"])
        return messages

    def append_user_message(self, content: str) -> None:
        data = {
            "message_id": self.message.id,
            "message": {
                "role": "user",
                "content": content,
            },
        }
        self.append_message(data)

    def append_assistant_message(self, content: str) -> None:
        data = {
            "message_id": self.res_message.id,
            "message": {
                "role": "assistant",
                "content": content,
            },
        }
        self.append_message(data)

    def append_tool_calls(self, tool_calls: list[dict]) -> None:
        data = {
            "message_id": self.res_message.id,
            "message": {
                "role": "assistant",
                "tool_calls": tool_calls,
            },
        }
        self.append_message(data)

    def append_tool_message(self, tool_call_id: str, content: str) -> None:
        data = {
            "message_id": self.res_message.id,
            "message": {
                "role": "tool",
                "content": content,
                "tool_call_id": tool_call_id,
            },
        }
        self.append_message(data)

    def append_message(self, data: dict) -> None:
        role = data["message"]["role"]
        self.role_check(role)
        self.db.append_message(self.guild.name, self.key, data)

    async def handle_tool_calls(self, tool_calls: "list[ChoiceDeltaToolCall]") -> None:
        embed = Embed(title="기능 호출", color=color.BASE)
        for tool_call in tool_calls:
            if tool_call.type == "function":
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments
                response = await self.tool_handler.process(function_name, function_args)
                self.append_tool_message(tool_call.id, response)
                name, value = await self.tool_handler.get_display(function_name)
                embed.add_field(name=name, value=value, inline=True)
        await self.res_message.edit(content="", embed=embed)

    def message_line(self, role: str, content: str) -> dict:
        self.role_check(role)
        return {"role": role, "content": content}

    def role_check(self, role: str) -> None:
        if role not in self.role_list:
            raise ValueError(f"role must be one of {self.role_list}")
