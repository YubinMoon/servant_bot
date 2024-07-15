from typing import TYPE_CHECKING

from langchain_core.messages import AIMessageChunk, AnyMessage, HumanMessage
from typing_extensions import TypedDict

from database.chat import get_thread_info
from database.user import get_used_tokens, set_used_tokens
from error.chat import NoAITypeError
from utils.logger import get_logger

from ..chat.agent import get_agent_by_name
from ..chat.callback import CalcTokenCallback, ChatCallback
from ..chat.graph import get_basic_app
from ..chat.manager import DiscordManager
from .base import BaseMessageHandler

if TYPE_CHECKING:
    from discord import Message

    from bot import ServantBot

logger = get_logger(__name__)


class ContentData(TypedDict):
    thinking: str = ""
    answer: str = ""


class ChatHandler(BaseMessageHandler):
    # base_response_txt = "생각 중..."

    def __init__(self, bot: "ServantBot", message: "Message") -> None:
        super().__init__(bot, message)
        self.discord = DiscordManager(self.channel)

    async def action(self):
        # thread_info = await get_thread_info(self.guild.name, self.key)
        # if thread_info is None:
        #     raise NoAITypeError("Thread info is not found.")
        # agent_name = thread_info.get("agent", "error")
        # agent = get_agent_by_name(agent_name)
        # await agent(self.message, thread_info).run()
        # await self.record_tokens(self.token_callback.to_dict())

        app = get_basic_app("claude-3-5-sonnet-20240620")

        messages = {"messages": self.get_message()}
        config = {"configurable": {"thread_id": self.key}}
        result = AIMessageChunk(content="")
        async with self.channel.typing():
            async for event in app.astream_events(
                messages, config=config, version="v2"
            ):
                kind = event["event"]
                tags = event.get("tags", [])
                if kind == "on_chat_model_stream" and "agent_node" in tags:
                    data = event["data"]
                    if data["chunk"]:
                        result += data["chunk"]
                        answer = self.chunk_parser(result)
                        await self.discord.send(answer)

    def chunk_parser(self, chunk: AIMessageChunk) -> str:
        content_data = self.content_parser(chunk.content)
        return content_data.get("answer", "")

    def content_parser(self, content: str) -> ContentData:
        result = {}
        current_tag = None
        current_text = ""

        i = 0
        while i < len(content):
            if content[i] == "<":
                if current_tag:
                    result[current_tag] = current_text.strip()
                    current_text = ""
                    current_tag = None

                end = content.find(">", i)
                if end == -1:
                    break

                tag = content[i + 1 : end]
                if not tag.startswith("/"):
                    current_tag = tag

                i = end + 1
            else:
                current_text += content[i]
                i += 1

        if current_tag:
            result[current_tag] = current_text.strip()

        return ContentData(**result)

    def get_message(self) -> list[AnyMessage]:
        user_message = HumanMessage(content=self.message.content)
        return [user_message]
