from typing import TYPE_CHECKING

from discord import Embed

from utils import color
from utils.logger import get_logger

from .base import BaseMessageHandler
from .error import UnknownCommandError

if TYPE_CHECKING:
    from discord import Message

    from bot import ServantBot


class BaseCommand:
    logger_name = "base_command"
    name = "base"

    def __init__(
        self,
        handler: "CommandHandler",
        args: list[str] = [],
    ):
        self.handler = handler
        self.args = args
        self.logger = get_logger(self.logger_name)

    async def run(self):
        raise NotImplementedError


class CommandList(BaseCommand):
    logger_name = "command_list_command"
    name = ""

    def __init__(
        self,
        handler: "CommandHandler",
        args: list[str] = [],
    ):
        super().__init__(handler, args)

    async def run(self):
        text = self.get_text()
        await self.handler.thread.send(text)

    def get_text(self):
        text = [
            "## 명령어 목록",
            "- ?: 명령어 목록을 보여줍니다.",
            "- ?system: 시스템 메시지를 확인합니다.",
            "- ?system `[str]`: 시스템 메시지를 `[str]`로 변경합니다.",
            "- ?retry: 이전 응답을 다시 생성합니다. (기존 응답은 삭제됩니다.)",
        ]

        return "\n".join(text)


class System(BaseCommand):
    logger_name = "system_command"
    name = "system"

    def __init__(
        self,
        handler: "CommandHandler",
        args: list[str] = [],
    ):
        super().__init__(handler, args)
        self.new_text = " ".join(args)

    async def run(self):
        self.logger.info(f"new_text: a{self.new_text}a")
        if self.new_text == "":
            await self.show_system_message()
        else:
            await self.set_system_message()

    async def show_system_message(self):
        guild_name = self.handler.guild.name
        key = self.handler.key

        system_message = self.handler.db.get_system_message(guild_name, key)

        if system_message is None:
            system_message = "`시스템 메시지가 없어요.`"

        embed = Embed(
            title="시스템 메시지",
            description=system_message,
            color=color.BASE,
        )
        await self.handler.thread.send(embed=embed)

    async def set_system_message(self):
        guild_name = self.handler.guild.name
        key = self.handler.key

        old_text = self.handler.db.get_system_message(guild_name, key)
        if old_text is None:
            old_text = "`시스템 메시지가 없어요.`"

        self.handler.db.set_system_message(guild_name, key, self.new_text)
        embed = Embed(
            title="시스템 메시지 변경",
            color=color.BASE,
        )
        embed.add_field(name="변경 전", value=old_text, inline=False)
        embed.add_field(name="변경 후", value=self.new_text, inline=False)
        await self.handler.thread.send(embed=embed)


class Retry(BaseCommand):
    logger_name = "retry_command"
    name = "retry"

    def __init__(
        self,
        handler: "CommandHandler",
        args: list[str] = [],
    ):
        super().__init__(handler, args)

    async def run(self):
        text = self.get_text()
        await self.handler.thread.send(text)

    def get_text(self):
        text = [
            "## 재시도",
            "이전 명령어를 다시 시도합니다.",
        ]

        return "\n".join(text)


class CommandHandler(BaseMessageHandler):
    logger_name = "command_handler"
    commands: list[type[BaseCommand]] = [
        CommandList,
        System,
        Retry,
    ]

    def __init__(self, bot: "ServantBot", message: "Message") -> None:
        super().__init__(bot, message)

    async def action(self):
        obj = self.parse_command()
        await obj.run()

    def parse_command(self) -> BaseCommand:
        content = self.message.content[1:]
        command = content.split(" ")[0]
        args = content.split(" ")[1:]
        for command_class in self.commands:
            if command_class.name == command:
                return command_class(self, args)
        else:
            raise UnknownCommandError(
                f"Unknown command: {command} by {self.message.author}."
            )
