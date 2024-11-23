from typing import TYPE_CHECKING

from error.chat import ChatBaseError
from utils.hash import generate_key
from utils.logger import get_logger

if TYPE_CHECKING:
    from discord import Embed, Message
    from discord.ext.commands import Context

    from bot import ServantBot


class BaseHandler:
    logger_name = "base_handler"

    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot
        self.logger = get_logger(self.logger_name)

    async def run(self, *args, **kwargs):
        try:
            await self.action(*args, **kwargs)
        except ChatBaseError as e:
            await self.send_error_message(e.get_embed())
            self.logger.error(e)

    async def action(self):
        raise NotImplementedError

    async def send_error_message(self, embed: "Embed") -> None:
        raise NotImplementedError


class BaseMessageHandler(BaseHandler):
    logger_name = "base_message_handler"

    def __init__(self, bot: "ServantBot", message: "Message") -> None:
        super().__init__(bot)
        if message.guild is None:
            raise ValueError("Guild is not found.")
        self.author = message.author
        self.message = message
        self.channel = message.channel
        self.guild = message.guild
        self.key: str = generate_key(str(self.channel.id), 6)

    async def send_error_message(self, embed: "Embed") -> None:
        await self.channel.send(embed=embed, silent=True)


class BaseCommandHandler(BaseHandler):
    logger_name = "base_command_handler"

    def __init__(self, bot: "ServantBot", context: "Context") -> None:
        super().__init__(bot)
        self.context = context
        self.guild = context.guild
        self.author = context.author
        self.channel = context.channel

    async def send_error_message(self, embed: "Embed") -> None:
        await self.context.send(embed=embed, ephemeral=True, silent=True)
