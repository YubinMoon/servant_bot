from typing import TYPE_CHECKING

from database.chat import get_thread_info
from database.user import get_used_tokens, set_used_tokens

from ..agent.model import get_template_agent
from ..chat.callback import CalcTokenCallback, ChatCallback
from ..error import NoAITypeError
from .base import BaseMessageHandler

if TYPE_CHECKING:
    from discord import Message

    from bot import ServantBot


class ChatHandler(BaseMessageHandler):
    logger_name = "chat_handler"
    base_response_txt = "생각 중..."

    def __init__(self, bot: "ServantBot", message: "Message") -> None:
        super().__init__(bot, message)
        self.token_callback = CalcTokenCallback()
        self.chat_callback = ChatCallback(self.message)

    async def action(self):
        thread_info = await get_thread_info(self.guild.name, self.key)
        if thread_info is None:
            raise NoAITypeError("Thread info is not found.")
        callbacks = [self.token_callback, self.chat_callback]
        agent_name = thread_info.get("agent", "error")
        agent = get_template_agent(
            agent_name,
            self.message,
            thread_info,
            callbacks,
        )
        await agent.run()
        data = self.token_callback.to_dict()
        print(data)
        await self.record_tokens(self.token_callback.to_dict())

    async def record_tokens(self, usage: dict[str, int]) -> None:
        data = await get_used_tokens(self.author.global_name)
        if data is None:
            data = dict()

        new_data = usage.copy()

        new_data["prompt_tokens"] += int(data.get("prompt_tokens", 0))
        new_data["completion_tokens"] += int(data.get("completion_tokens", 0))
        new_data["tool_tokens"] += int(data.get("tool_tokens", 0))
        new_data["total_tokens"] += int(data.get("total_tokens", 0))
        new_data["prompt_cost"] += int(data.get("prompt_cost", 0))
        new_data["completion_cost"] += int(data.get("completion_cost", 0))
        new_data["tool_cost"] += int(data.get("tool_cost", 0))
        new_data["total_cost"] += int(data.get("total_cost", 0))

        await set_used_tokens(self.author.global_name, new_data)
