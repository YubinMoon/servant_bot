import asyncio
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Message, Thread


class DiscordManager:
    def __init__(self, thread: "Thread") -> None:
        self.thread = thread
        self.chat_message: Message = None
        self.tool_message: Message = None
        self.chat_text = ""
        self.buffer_time = 0.5
        self.buffer = deque()
        self.sended_content = ""
        self.new_content = ""
        self.is_running = False
        self.is_complete = False

    async def send(self, content: str):
        self.new_content = content
        if not self.is_running and self.sended_content != self.new_content:
            self.is_running = True
            asyncio.create_task(self._send_message())

    async def _send_message(self):
        while self.sended_content != self.new_content:
            if self.chat_message is None:
                self.chat_message = await self.thread.send(content=self.new_content)
            else:
                await self.chat_message.edit(content=self.new_content)
            self.sended_content = self.new_content
            await asyncio.sleep(self.buffer_time)
        self.is_running = False
