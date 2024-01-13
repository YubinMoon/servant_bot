import discord.ext.commands
import redis
import logging


class DatabaseManager:
    def __init__(self, bot) -> None:
        self.bot: discord.ext.commands.Bot = bot
        self.database: redis.Redis = bot.database
        self.logger: logging.Logger = bot.logger
