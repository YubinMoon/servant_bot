import os
from time import time
from typing import TYPE_CHECKING

import openai

from database import ChatDataManager
from utils.logger import get_logger

from .base import BaseMessageHandler
from .error import UnknownCommandError

if TYPE_CHECKING:
    from discord import Channel, Message
    from discord.abc import MessageableChannel

    from bot import ServantBot


class BaseCommand:
    logger_name = "base_command"

    def __init__(self, channel: "MessageableChannel"):
        self.channel = channel
        self.logger = get_logger(self.logger_name)

    async def run(self):
        raise NotImplementedError


class CommandList(BaseCommand):
    logger_name = "command_list_command"

    def __init__(self, channel: "MessageableChannel"):
        super().__init__(channel)

    async def run(self):
        text = self.get_text()
        await self.channel.send(text)

    def get_text(self):
        text = [
            "## 명령어 목록",
            "- ?: 명령어 목록을 보여줍니다.",
            "- ?system: 시스템 메시지를 확인합니다.",
            "- ?system `[str]`: 시스템 메시지를 `[str]`로 변경합니다.",
        ]

        return "\n".join(text)


class CommandHandler(BaseMessageHandler):
    logger_name = "command_handler"

    def __init__(self, bot: "ServantBot", message: "Message") -> None:
        super().__init__(bot, message)

    async def action(self):
        obj = self.parse_command()
        await obj.run()

    def parse_command(self) -> BaseCommand:
        content = self.message.content[1:]
        command = content.split(" ")[0]
        args = content.split(" ")[1:]
        if command == "":
            return CommandList(self.thread)
        else:
            raise UnknownCommandError(
                f"Unknown command: {command} by {self.message.author}."
            )

    def send_command_list(self):
        pass
