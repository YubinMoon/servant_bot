import platform
from datetime import datetime
from time import time

import discord
from discord.ext import commands
from discord.ext.commands import Context

from bot import ServantBot
from config import config
from utils.command import get_command_description, get_group_command_description
from utils.logger import get_logger


class General(commands.Cog, name="general"):
    def __init__(self, bot: ServantBot) -> None:
        self.bot = bot
        self.logger = get_logger("general")

        self._restrict = False
        self._start_time_val = datetime.now()
        self._start_time_lol = datetime.now()

    @commands.hybrid_command(name="help", description="모든 명령어를 보여줍니다.")
    async def help(self, context: Context) -> None:
        prefix = config["prefix"]
        embed = discord.Embed(
            title="Help", description="List of available commands:", color=0xBEBEFE
        )
        for i in self.bot.cogs:
            if i == "owner" and not (await self.bot.is_owner(context.author)):
                continue
            cog = self.bot.get_cog(i)
            cog_commands = cog.get_commands()
            data = []
            for command in cog_commands:
                if isinstance(command, commands.core.Group):
                    group_commands = command
                    for group_command in group_commands.commands:
                        data.append(
                            get_group_command_description(
                                prefix, command, group_command
                            )
                        )
                else:
                    data.append(get_command_description(prefix, command))
            help_text = "\n".join(data)
            embed.add_field(
                name=i.capitalize(), value=f"```{help_text}```", inline=False
            )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="botinfo",
        description="봇의 정보를 보여줍니다.",
    )
    async def botinfo(self, context: Context) -> None:
        embed = discord.Embed(
            description="여러가지 기능을 담은 도우미 봇\n[Krypton's](https://krypton.ninja) template을 기반으로 제작되었습니다.",
            color=0xBEBEFE,
        )
        embed.set_author(name="Bot Information")
        embed.add_field(name="Owner:", value="yubinmoon", inline=True)
        embed.add_field(
            name="Python Version:", value=f"{platform.python_version()}", inline=True
        )
        embed.add_field(
            name="Prefix:",
            value=f"/ (Slash Commands) or {config['prefix']} for normal commands",
            inline=False,
        )
        embed.set_footer(text=f"Requested by {context.author}")
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="serverinfo",
        description="서버의 정보를 보여줍니다.",
    )
    async def serverinfo(self, context: Context) -> None:
        roles = [role.name for role in context.guild.roles]
        if len(roles) > 50:
            roles = roles[:50]
            roles.append(f">>>> Displayin [50/{len(roles)}] Roles")
        roles = ", ".join(roles)

        embed = discord.Embed(
            title="**Server Name:**", description=f"{context.guild}", color=0xBEBEFE
        )
        if context.guild.icon is not None:
            embed.set_thumbnail(url=context.guild.icon.url)
        embed.add_field(name="Server ID", value=context.guild.id)
        embed.add_field(name="Member Count", value=context.guild.member_count)
        embed.add_field(
            name="Text/Voice Channels", value=f"{len(context.guild.channels)}"
        )
        embed.add_field(name=f"Roles ({len(context.guild.roles)})", value=roles)
        embed.set_footer(text=f"Created at: {context.guild.created_at}")
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="ping",
        description="봇의 상태를 확인합니다.",
    )
    async def ping(self, context: Context) -> None:
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="invite",
        description="봇을 초대할 수 있는 링크를 보여줍니다.",
    )
    async def invite(self, context: Context) -> None:
        embed = discord.Embed(
            description=f"저를 서버에 초대해 주세요. [클릭]({config['invite_link']}).",
            color=0xD75BF4,
        )
        try:
            await context.author.send(embed=embed)
            await context.send("개인 메시지로 초대 링크를 보냈어요! 📩", ephemeral=True)
        except discord.Forbidden:
            await context.send(embed=embed, ephemeral=True)


async def setup(bot: ServantBot) -> None:
    await bot.add_cog(General(bot))
