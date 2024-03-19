import asyncio
from typing import TYPE_CHECKING

from discord import Embed, HTTPException, NotFound

from utils import color
from utils.logger import get_logger

from .base import BaseMessageHandler
from .chat.manager import ChatManager
from .error import NoHistoryError, UnknownCommandError

if TYPE_CHECKING:
    from discord import Message

    from bot import ServantBot


class BaseCommand:
    logger_name = "base_command"
    name = "base"

    def __init__(self, handler: "CommandHandler", args: list[str] = []):
        self.args = args
        self.logger = get_logger(self.logger_name)
        self.bot = handler.bot
        self.db = handler.db
        self.guild = handler.guild
        self.thread = handler.thread
        self.message = handler.message
        self.key = handler.key

    async def run(self):
        raise NotImplementedError


class CommandList(BaseCommand):
    logger_name = "command_list_command"
    name = ""

    def __init__(self, handler: "CommandHandler", args: list[str] = []):
        super().__init__(handler, args)

    async def run(self):
        text = self.get_text()
        await self.thread.send(text)

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

    def __init__(self, handler: "CommandHandler", args: list[str] = []):
        super().__init__(handler, args)
        self.new_text = " ".join(args)

    async def run(self):
        self.logger.info(f"new_text: a{self.new_text}a")
        if self.new_text == "":
            await self.show_system_message()
        else:
            await self.set_system_message()

    async def show_system_message(self):

        system_message = self.get_system_message()

        embed = Embed(
            title="시스템 메시지",
            description=system_message,
            color=color.BASE,
        )
        await self.thread.send(embed=embed)

    async def set_system_message(self):
        old_system_message = self.get_system_message()

        self.db.set_system_message(self.guild.name, self.key, self.new_text)
        embed = Embed(
            title="시스템 메시지 변경",
            color=color.BASE,
        )
        embed.add_field(name="변경 전", value=old_system_message, inline=False)
        embed.add_field(name="변경 후", value=self.new_text, inline=False)
        await self.thread.send(embed=embed)

    def get_system_message(self):
        system_message = self.db.get_system_message(self.guild.name, self.key)
        if system_message is None:
            system_message = "`시스템 메시지가 없어요.`"
        return system_message


class Retry(BaseCommand):
    logger_name = "retry_command"
    name = "retry"

    def __init__(
        self,
        handler: "CommandHandler",
        args: list[str] = [],
    ):
        super().__init__(handler, args)
        self.chat_manager = ChatManager(self.bot, self.thread)

    async def run(self):
        if await self.is_lock():
            return
        try:
            self.db.lock(self.guild.name, self.key)
            await self.delete_old_response()
            await self.message.delete()
            await self.chat_manager.run_task()
        except Exception as e:
            raise e
        finally:
            self.db.unlock(self.guild.name, self.key)

    async def is_lock(self) -> bool:
        if self.db.has_lock(self.guild.name, self.key):
            embed = Embed(
                title="아직 답변이 완료되지 않았어요.",
            )
            reply_msg = await self.message.reply(embed=embed)
            await asyncio.sleep(delay=3)
            await reply_msg.delete()
            await self.message.delete()
            return True
        return False

    async def delete_old_response(self):
        old_response = self.db.get_messages(self.guild.name, self.key)
        if old_response == []:
            raise NoHistoryError("No history found.")
        last_user_message_index = self.get_last_user_message_index(old_response)
        self.db.trim_messages(self.guild.name, self.key, last_user_message_index)
        useless_messages = old_response[last_user_message_index + 1 :]

        useless_messages_id = set([data["message_id"] for data in useless_messages])
        for message_id in useless_messages_id:
            try:
                message = await self.thread.fetch_message(message_id)
                self.logger.info(
                    f"Deleting message: ({message_id}) - {message.content}"
                )
                await message.delete()
            except HTTPException:
                self.logger.warning(f"Message not found: {message_id}")

    def get_last_user_message_index(self, old_response: list[dict]):
        for i in range(len(old_response) - 1, 0, -1):
            if old_response[i]["message"]["role"] == "user":
                return i
        return 0


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
