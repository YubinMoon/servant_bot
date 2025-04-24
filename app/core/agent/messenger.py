from typing import TYPE_CHECKING, Callable, List

if TYPE_CHECKING:
    from discord import Message, Thread


class Messenger:
    def __init__(self, thread: "Thread", splitter: Callable[[str], List[str]]):
        self.thread = thread
        self.splitter = splitter
        self.messages: "List[Message]" = []
        self._contents: List[str] = []
        self._pending_parts: List[str] = []

    def set_content(self, content: str):
        self._pending_parts = self.splitter(content)

    async def update_message(self):
        for i, part in enumerate(self._pending_parts):
            if i < len(self.messages):
                if self._contents[i] != part:
                    await self.messages[i].edit(content=part)
                    self._contents[i] = part
            else:
                msg = await self.thread.send(content=part)
                self.messages.append(msg)
                self._contents.append(part)
