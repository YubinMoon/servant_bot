import logging
from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from app.core.database import get_session

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from app.bot import ServantBot

logger = logging.getLogger(__name__)


class Agent(commands.Cog, name="agent"):
    def __init__(self, bot: "ServantBot") -> None:
        self.bot = bot
