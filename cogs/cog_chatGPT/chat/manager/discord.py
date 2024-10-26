import asyncio
import io
from collections import deque
from typing import TYPE_CHECKING

from discord import Embed, File
from langchain_core.tools import ToolCall

from utils import color
from utils.logger import get_logger

if TYPE_CHECKING:
    from discord import Message, Thread

logger = get_logger(__name__)


class DiscordManager:
    def __init__(self, thread: "Thread") -> None:
        self.thread = thread
        self.chat_message: Message = None
        self.tool_message: Message = None
        self.send_cool_time = 0.5
        self.sended_content = ""
        self.new_content = ""
        self.called_tools: list[ToolCall] = []
        self.is_running = False

    async def send_message(self, content: str):
        self.new_content = content[:1500] + "..." if len(content) > 1500 else content
        if not self.is_running and self.sended_content != self.new_content:
            self.is_running = True
            logger.debug("new send process start")
            asyncio.create_task(self._semd_process())

    async def done_message(self, content: str):
        self.new_content = content[:1500] + "..." if len(content) > 1500 else content
        while self.is_running:
            await asyncio.sleep(0.1)

        if len(content) > 1500:
            logger.debug("large content send process start")
            _file = io.BytesIO(content.encode("utf-8"))
            await self.chat_message.edit(
                content="메시지가 너무 길어 파일로 전송합니다.",
                attachments=[File(_file, filename="answer.txt")],
            )
        elif self.sended_content != self.new_content:
            logger.debug("done send process start")
            asyncio.create_task(self._semd_process())
        self.chat_message = None

    async def send_tool_message(self, tool_calls: list[ToolCall]):
        if tool_calls:
            self.called_tools.extend(tool_calls)
            embed = Embed(title="기능 호출", color=color.BASE)
            for tool in self.called_tools:
                embed.add_field(
                    name=tool.get("name", ""),
                    value=f"`{tool.get('args','')}`",
                    inline=False,
                )
            if self.tool_message:
                await self.tool_message.edit(embed=embed)
            else:
                self.tool_message = await self.thread.send(embed=embed)

    async def _semd_process(self):
        while self.sended_content != self.new_content:

            self.sended_content = self.new_content
            if self.chat_message is None:
                self.chat_message = await self.thread.send(content=self.sended_content)
            else:
                await self.chat_message.edit(content=self.sended_content)
            await asyncio.sleep(self.send_cool_time)
        self.is_running = False
