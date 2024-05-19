from typing import TYPE_CHECKING

from database.chat import get_thread_info

from ..agent.model import get_template_agent
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

    async def action(self):
        thread_info = await get_thread_info(self.guild.name, self.key)
        if thread_info is None:
            raise NoAITypeError("Thread info is not found.")
        agent_name = thread_info.get("agent", "error")
        agent = get_template_agent(agent_name, self.message, thread_info)
        await agent.run()
