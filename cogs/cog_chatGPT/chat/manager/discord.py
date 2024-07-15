import asyncio
from collections import deque
from typing import TYPE_CHECKING

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
        self.is_running = False

    async def send_message(self, content: str):
        self.new_content = content
        if not self.is_running and self.sended_content != self.new_content:
            self.is_running = True
            logger.debug("new send process start")
            asyncio.create_task(self._semd_process())

    async def _semd_process(self):
        while self.sended_content != self.new_content:
            self.sended_content = self.new_content
            if self.chat_message is None:
                self.chat_message = await self.thread.send(content=self.sended_content)
            else:
                await self.chat_message.edit(content=self.sended_content)
            await asyncio.sleep(self.send_cool_time)
        self.is_running = False
