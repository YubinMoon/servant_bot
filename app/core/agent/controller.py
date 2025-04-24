import base64
import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import requests

from app.common.utils.text_splitter import split_into_chunks

if TYPE_CHECKING:
    from discord import Attachment, Message, Thread
    from discord.ext.commands import Context


logger = logging.getLogger(__name__)


class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"


@dataclass
class MessageData:
    type: MessageType
    content: str

    def to_content(self) -> dict[str, str]:
        if self.type == MessageType.TEXT:
            return {"type": "input_text", "text": self.content}
        elif self.type == MessageType.IMAGE:
            return {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{self.content}",
            }


async def setup_new_chat(
    context: "Context", title: str, message_content: str
) -> "Thread":
    message = await context.send(message_content)
    thread = await message.create_thread(name=title)
    return thread


async def _parse_attachment(
    attachment: "Attachment",
) -> MessageData | None:
    if attachment.content_type.startswith("image/"):
        try:
            response = requests.get(attachment.url)
            response.raise_for_status()
        except Exception:
            logger.warning(f"Failed to download image: {attachment.url}")
            return None
        b64_bytes = base64.b64encode(response.content)
        return MessageData(type=MessageType.IMAGE, content=b64_bytes.decode("utf-8"))
    elif (
        attachment.content_type.startswith("text/")
        or attachment.content_type == "application/json"
        or attachment.content_type == "application/xml"
    ):
        file_name = attachment.filename
        raw_content = await attachment.read()
        file_content = raw_content.decode("utf-8")
        content = f"<file name={file_name}>\n{file_content}\n</file>"
        return MessageData(type=MessageType.TEXT, content=content)
    else:
        file_type = attachment.content_type
        file_name = attachment.filename
        logger.warning(f"Unsupported file type: {file_type} for file: {file_name}")
        return None


async def parse_message(message: "Message"):
    messages: list[MessageData] = []
    for attachment in message.attachments or ():
        if parsed := await _parse_attachment(attachment):
            messages.append(parsed)
    if message.content:
        messages.append(MessageData(type=MessageType.TEXT, content=message.content))
    return messages


if __name__ == "__main__":
    data = MessageData(
        type=MessageType.TEXT,
        content="Hello, world!",
    )
    print(data)
    print(data.to_content())
