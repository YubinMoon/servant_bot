import base64
from textwrap import dedent
from typing import TYPE_CHECKING

from langchain_core.documents import Document
from langchain_core.messages import AIMessageChunk, AnyMessage, HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing_extensions import TypedDict

from utils.chat import get_token_count
from utils.logger import get_logger

from ..chat.graph import get_basic_app
from ..chat.manager import DiscordManager
from ..chat.memory import get_memory
from .base import BaseMessageHandler

if TYPE_CHECKING:
    from discord import Attachment, Message

    from bot import ServantBot

logger = get_logger(__name__)


class ContentData(TypedDict):
    thinking: str = ""
    answer: str = ""


class ChatHandler(BaseMessageHandler):
    def __init__(self, bot: "ServantBot", message: "Message") -> None:
        super().__init__(bot, message)
        self.discord = DiscordManager(self.channel)
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=[".", "!", "?", "\n", ",", " "],
            chunk_size=800,
            chunk_overlap=400,
            length_function=get_token_count,
        )
        self.memory = get_memory(self.channel)

    async def action(self):
        app = get_basic_app("claude-3-5-sonnet-20240620", self.memory)

        messages = await self.get_message()
        _input = {"messages": messages}
        logger.debug(f"user input: {_input}")
        config = {"configurable": {"thread_id": self.key}}
        result = AIMessageChunk(content="")
        async with self.channel.typing():
            async for event in app.astream_events(_input, config=config, version="v2"):
                kind = event["event"]
                tags = event.get("tags", [])
                if kind == "on_chat_model_stream" and "agent_node" in tags:
                    data = event["data"]
                    if data["chunk"]:
                        result += data["chunk"]
                        answer = self.chunk_parser(result)
                        await self.discord.send_message(answer)
        logger.debug(f"answer: {result.content}")
        logger.info(f"{self.message.author} - token usage: {result.usage_metadata}")

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

    async def get_message(self) -> list[AnyMessage]:
        file_names = await self.load_text_attachments()
        media_contents = await self.load_media_attachments()
        contents = []
        if file_names:
            contents.append(
                {"type": "text", "text": f"<file>\n{file_names}\n</file>\n"}
            )
        if media_contents:
            contents.extend(media_contents)
        contents.append(
            {"type": "text", "text": f"<user>\n{self.message.content}\n</user>"}
        )
        return [HumanMessage(content=contents)]

    async def load_text_attachments(self):
        text_file_types = (
            "text/",
            "application/json",
            "application/xml",
        )

        file_names = []

        for attachment in self.message.attachments:
            file_type = attachment.content_type.split()[0]
            if file_type.startswith(text_file_types):
                await self._load_text_file(attachment)
            elif file_type.startswith("image/"):
                await self._load_image_file(attachment)
            else:
                continue
            file_names.append(attachment.filename)
        return file_names

    async def load_media_attachments(self):
        contents = []
        for attachment in self.message.attachments:
            file_type = attachment.content_type.split()[0]
            if file_type.startswith("image/"):
                content = await self._load_image_file(attachment)
            else:
                continue
            contents.append(content)
        return contents

    async def _load_text_file(self, attachment: "Attachment"):
        contents = await attachment.read()
        contents = contents.decode("utf-8")
        document = Document(
            page_content=contents,
            metadata={"source": attachment.filename, "page": 0},
        )
        await self._insert_content([document])

    async def _load_image_file(self, attachment: "Attachment"):
        image_data = await attachment.read()
        img_base64 = base64.b64encode(image_data).decode()
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_base64}",
            },
        }

    async def _insert_content(self, documents: "list[Document]"):
        total_token = 0
        for document in documents:
            total_token += get_token_count(document.page_content)

        splitted_docs = self.text_splitter.split_documents(documents)
        await self.memory.aadd_documents(splitted_docs)
        await self.message.reply(
            dedent(
                f"""
                입력된 파일을 {len(documents)}개로 분할하여 저장합니다.
                저장된 파일은 자동 선별되어 사용됩니다.
                """
            )
        )
