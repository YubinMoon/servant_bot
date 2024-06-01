import os
import platform
from time import time

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from bot import ServantBot
from utils.command import get_command_description, get_group_command_description
from utils.logger import get_logger


class General(commands.Cog, name="general"):
    def __init__(self, bot: ServantBot) -> None:
        self.bot = bot
        self.config = bot.config
        self.logger = get_logger("general")

        self._restrict = False
        self.cooldown = time()

    @commands.hybrid_command(name="help", description="모든 명령어를 보여줍니다.")
    async def help(self, context: Context) -> None:
        prefix = self.bot.config["prefix"]
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
            value=f"/ (Slash Commands) or {self.bot.config['prefix']} for normal commands",
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
            description=f"저를 서버에 초대해 주세요. [클릭]({self.bot.config['invite_link']}).",
            color=0xD75BF4,
        )
        try:
            await context.author.send(embed=embed)
            await context.send("개인 메시지로 초대 링크를 보냈어요! 📩", ephemeral=True)
        except discord.Forbidden:
            await context.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="restrict",
        description="봇의 소스 코드를 보여줍니다.",
    )
    @app_commands.choices(
        onoff=[
            app_commands.Choice(name="on", value="on"),
            app_commands.Choice(name="off", value="off"),
        ]
    )
    async def restrict(self, context: Context, onoff: str) -> None:
        if onoff == "on":
            self._restrict = True
            await context.send(
                f"{os.getenv('PJY_NAME')} 몰컴 감시기 가동", ephemeral=True
            )
        elif onoff == "off":
            self._restrict = False
            await context.send(
                f"{os.getenv('PJY_NAME')} 몰컴 감시기 중지", ephemeral=True
            )
        else:
            await context.send("잘못된 입력입니다.")

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        guild = before.guild
        first_channel = guild.text_channels[0]
        test_channel = guild.text_channels[-1]
        self.logger.info(f"{before.activity} -> {after.activity}")

        if self._restrict:
            if after.id == int(os.getenv("PJY_ID")) and guild.id == int(
                os.getenv("PJY_GUILD_ID")
            ):
                # 박정인 온라인 확인
                if (
                    before.desktop_status != after.desktop_status
                    and after.desktop_status == discord.Status.online
                ):
                    self.logger.info(f"{os.getenv('PJY_NAME')} 컴퓨터 온라인 검거")
                    await test_channel.send(
                        f"{os.getenv('PJY_NAME')} 컴퓨터 온라인 검거"
                    )
                if before.activity != after.activity:
                    if "VALORANT" in str(after.activity):
                        if after.voice is None:
                            self.logger.info(f"{os.getenv('PJY_NAME')} 게임 시작")
                            await first_channel.send(
                                "WARNING! WARNING! WARNING!\n"
                                f"{after.mention}몰로란트 검거\n"
                                "WARNING! WARNING! WARNING!"
                            )


async def setup(bot: ServantBot) -> None:
    await bot.add_cog(General(bot))
