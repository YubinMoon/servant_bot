import os
import platform
import random
import sys
import traceback

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context

from .cogs import cog_list
from .common.logger import get_logger
from .core.database import create_db_and_tables

logger = get_logger(__name__)


class ServantBot(commands.Bot):
    def __init__(self, intents: discord.Intents) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(os.getenv("BOT_PREFIX", "!")),
            intents=intents,
            help_command=None,
        )

    async def load_db(self) -> None:
        try:
            create_db_and_tables()
        except:
            logger.error("Failed to create the database and tables")
            logger.debug(traceback.format_exc())
            sys.exit(1)

    async def load_cogs(self) -> None:
        for cog in cog_list:
            try:
                await self.add_cog(cog(self))
                logger.info(f"Loaded extension '{cog.__name__}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                logger.error(f"Failed to load extension {cog.__name__}\n{exception}")
                logger.debug(traceback.format_exc())

    @tasks.loop(minutes=1.0)
    async def status_task(self) -> None:
        """
        Setup the game status task of the bot.
        """
        statuses = self.get_status_list()
        await self.change_presence(activity=discord.Game(random.choice(statuses)))

    def get_status_list(self) -> list[str]:
        try:
            with open("status.txt", "r") as f:
                return f.read().split("\n")
        except FileNotFoundError:
            logger.warning("Status file not found, using default status")
            return ["limeskin"]

    @status_task.before_loop
    async def before_status_task(self) -> None:
        """
        Before starting the status changing task, we make sure the bot is ready
        """
        await self.wait_until_ready()

    async def setup_hook(self) -> None:
        """
        This will just be executed when the bot starts the first time.
        """
        if self.user is None:
            bot_user_name = "Unknown"
        else:
            bot_user_name = self.user.name
        logger.info(f"Logged in as {bot_user_name}")
        logger.info(f"discord.py API version: {discord.__version__}")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        logger.info("-------------------")
        await self.load_cogs()
        await self.load_db()
        self.status_task.start()

    async def on_ready(self) -> None:
        logger.info("Sync starting...")
        await self.tree.sync()
        logger.info("Sync complete")

    async def on_message(self, message: discord.Message) -> None:
        """
        The code in this event is executed every time someone sends a message, with or without the prefix

        :param message: The message that was sent.
        """
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_command_completion(self, context: Context) -> None:
        """
        The code in this event is executed every time a normal command has been *successfully* executed.

        :param context: The context of the command that has been executed.
        """
        if context.command is None:
            return
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if context.guild is not None:
            logger.info(
                f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            logger.info(
                f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
            )

    async def on_command_error(self, context: Context, error) -> None:
        """
        The code in this event is executed every time a normal valid command catches an error.

        :param context: The context of the normal command that failed executing.
        :param error: The error that has been faced.
        """
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = discord.Embed(
                description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                description="You are not the owner of the bot!", color=0xE02B2B
            )
            await context.send(embed=embed, ephemeral=True)
            if context.guild:
                logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
                )
            else:
                logger.warning(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
                )
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="You are missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to execute this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                description="I am missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to fully perform this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!",
                # We need to capitalize because the command arguments have no capital letter in the code and they are the first word in the error message.
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await context.send(embed=embed, ephemeral=True)
        elif isinstance(error, commands.errors.CommandNotFound):
            logger.warning(
                f"{context.author} (ID: {context.author.id}) tried to execute the invalid command '{context.invoked_with}'"
            )
