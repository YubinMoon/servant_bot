import logging
from typing import TYPE_CHECKING, Callable, List, Literal

from pydantic import BaseModel

if TYPE_CHECKING:
    from discord import Message, Thread

logger = logging.getLogger(__name__)


class MessagePart(BaseModel):
    content: str
    type: Literal["text", "image", "tool"]


class Messenger:
    def __init__(self, thread: "Thread", splitter: Callable[[str], List[str]]):
        self.thread = thread
        self.splitter = splitter
        self.messages: "List[Message]" = []
        self._sended_contents: List[str] = []
        self._pending_parts: List[str] = []
        self._contents: List[MessagePart] = []

    def _message_builder(self) -> str:
        result = ""
        for part in self._contents:
            if part.type == "text":
                result += f"{part.content}\n\n"
            elif part.type == "image":
                logger.warning("image part is not supported")
            elif part.type == "tool":
                result += f"{part.content}\n\n"
        return result.strip()

    def add_content(
        self, content: str, type: Literal["text", "image", "tool"] = "text"
    ):
        self._contents.append(MessagePart(content=content, type=type))

    def del_content(self):
        if self._contents:
            self._contents.pop()

    async def update_message(self):
        content = self._message_builder()
        if not content:
            return
        pending_parts = self.splitter(content)
        for i, part in enumerate(pending_parts):
            if i < len(self.messages):
                if self._sended_contents[i] != part:
                    await self.messages[i].edit(content=part)
                    self._sended_contents[i] = part
            else:
                msg = await self.thread.send(content=part)
                self.messages.append(msg)
                self._sended_contents.append(part)
