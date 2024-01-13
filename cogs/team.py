import logging
import random
import traceback
import discord
from discord.ext import commands
from discord.ext.commands import Context
from database import TeamDataManager


class TeamHandler:
    LANE = ["탑", "정글", "미드", "원딜", "서폿"]

    def __init__(self, bot) -> None:
        self.bot = bot
        self.logger: logging.Logger = bot.logger
        self.base_weight = [[10000 for _ in range(5)] for _ in range(5)]
        self.db = TeamDataManager(bot)
        self.multiple = 0.1
        self.messages: dict[int, discord.Message] = {}
        self.teams: dict[int, list[discord.Member]] = {}
        self.weights: dict[int, list[list[int]]] = {}

    async def start(self, context: Context) -> None:
        channel_id = context.channel.id
        embed = discord.Embed(
            title="새로운 팀이 생성되었습니다.",
            description="**/j** 명령어를 통해 등록해 주세요",
            color=0xBEBEFE,
        )
        embed.add_field(name="0/5", value="")
        embed.set_footer(text="/s로 팀을 구성합니다. /c로 팀 등록을 취소합니다.")
        message = await context.send(embed=embed)
        try:
            await self.db.start_team(channel_id, message.id)
            await self.join(context)
        except Exception as e:
            self.logger.error(e)
            embed = discord.Embed(
                title="팀 생성에 실패했습니다.",
                description="다시 시도해 주세요.",
                color=0xE02B2B,
            )
            await message.edit(embed=embed)

            error_embed = discord.Embed(
                title="ERROR LOG",
                description=f"```{traceback.format_exc()}```",
                color=0xE02B2B,
            )
            await context.send(embed=error_embed, ephemeral=True)
            traceback.print_exc()

    async def join(self, context: Context) -> None:
        channel_id = context.channel.id
        member = context.author
        if await self.db.get_team(channel_id) is None:
            await self.no_team_error(context)
        members = await self.db.get_members(channel_id)
        if member in members:
            await self.already_in_team_error(context)
        if len(members) >= 10:
            await self.max_team_error(context)

        await self.db.add_member(channel_id, member)
        await self.update_message(channel_id)

        embed = discord.Embed(
            description=f"{(await self.db.get_message(channel_id)).jump_url}에 {member.mention}님이 팀에 등록되었습니다.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    async def cancel_join(self, context: Context) -> None:
        channel_id = context.channel.id
        member = context.author
        if await self.db.get_team(channel_id) is None:
            await self.no_team_error(context)
        members = await self.db.get_members(channel_id)
        if member not in members:
            await self.already_not_in_team_error(context)

        await self.db.pop_member(channel_id, member)
        await self.update_message(channel_id)

        embed = discord.Embed(
            description=f"{member.mention}님이 팀 등록을 취소했습니다.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    async def update_message(self, channel_id: int) -> None:
        message = await self.db.get_message(channel_id)
        members = await self.db.get_members(channel_id)
        embed = message.embeds[0]
        embed.set_field_at(
            index=0,
            name=f"{len(members)}/{5 if len(members) <= 5 else 10}",
            value=" - ".join([member.mention for member in members]),
        )
        await message.edit(embed=embed)

    async def shuffle(self, context: Context) -> None:
        channel_id = context.channel.id
        if await self.db.get_team(channel_id) is None:
            await self.no_team_error(context)
        members = await self.db.get_members(channel_id)
        if len(members) not in [5, 10]:
            await self.max_team_error(context)

        if len(members) == 5:
            await self.shuffle_rank(context)
        elif len(members) == 10:
            await self.shuffle_custom(context)

    async def shuffle_rank(self, context: Context) -> None:
        channel_id = context.channel.id

        members = await self.db.get_members(channel_id)
        team = self.get_rank_team(channel_id)
        self.adjustment_weight(channel_id, team)
        embed = discord.Embed(
            description="새로운 팀을 구성했습니다.",
            color=0xBEBEFE,
        )
        for i, lane in enumerate(self.LANE):
            member_no = team.index(i)
            member = members[member_no]
            embed.add_field(name=lane, value=member.mention)
        await context.send(embed=embed)

    async def shuffle_custom(self, context: Context) -> None:
        channel_id = context.channel.id

        members = await self.db.get_members(channel_id)
        random.shuffle(members)
        embed = discord.Embed(
            description="새로운 팀을 구성했습니다.",
            color=0xBEBEFE,
        )
        embed.add_field(
            name="1팀", value="\n".join([member.mention for member in members[:5]])
        )
        embed.add_field(
            name="2팀", value="\n".join([member.mention for member in members[5:]])
        )
        await context.send(embed=embed)

    def get_rank_team(self, channel_id: int) -> list[int]:
        team = []
        weights = self.db.get_weights(channel_id)
        while len(set(team)) != 5:
            team.clear()
            for i in range(5):
                team.append(random.choices(range(5), weights=weights[i])[0])
        return team

    def adjustment_weight(self, channel_id: int, team: list[int]) -> None:
        weight = self.db.get_weights(channel_id)
        for member_no, lane_no in enumerate(team):
            remain = (weight[member_no][lane_no] * (1 - self.multiple)) // 4
            for i in range(5):
                if i == lane_no:
                    weight[member_no][i] -= remain * 4
                else:
                    weight[member_no][i] += remain
        self.db.set_weights(channel_id, weight)

    async def no_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            title="팀이 생성되지 않았습니다.",
            description="**/q** 팀을 생성해 주세요.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True)
        raise commands.CommandError("no rank team")

    async def already_in_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="이미 팀에 등록되었습니다.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True)
        raise commands.CommandError("already in rank team")

    async def already_not_in_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="팀에 등록되어 있지 않습니다.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True)
        raise commands.CommandError("already not in rank team")

    async def max_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="팀이 꽉 찼습니다.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True)
        raise commands.CommandError("max rank team")

    async def team_member_num_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="인원이 맞지 않습니다.\n\n5명 또는 10명이어야 합니다.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True)
        raise commands.CommandError("team member num error")


class Team(commands.Cog, name="team"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.handler = TeamHandler(bot)

    @commands.hybrid_group(name="team")
    async def team(self, context: Context) -> None:
        pass

    @team.command(name="start", description="새로운 팀 생성 (기존 팀 제거)")
    async def start(self, context: Context) -> None:
        try:
            await self.handler.start(context)
        except commands.CommandError as e:
            self.bot.logger.warning(e)

    @commands.hybrid_command(
        name="q", description="alias of /lol start", aliases=["ㅋ", "큐"]
    )
    async def alias_start(self, context: Context) -> None:
        await self.start(context)

    @team.command(name="join", description="생성된 팀에 참가")
    async def join(self, context: Context) -> None:
        try:
            await self.handler.join(context)
        except commands.CommandError as e:
            self.bot.logger.warning(e)

    @commands.hybrid_command(
        name="j", description="alias of /lol join", aliases=["ㅊ", "참", "참여", "참가"]
    )
    async def alias_join(self, context: Context) -> None:
        await self.join(context)

    @team.command(name="cancel", description="팀 참가 취소")
    async def cancel_join(self, context: Context) -> None:
        try:
            await self.handler.cancel_join(context)
        except commands.CommandError as e:
            self.bot.logger.warning(e)

    @commands.hybrid_command(
        name="c",
        description="alias of /lol cancel",
        aliases=["ㅊㅅ", "취", "취소"],
    )
    async def alias_cencel_join(self, context: Context) -> None:
        await self.cancel_join(context)

    @team.command(name="shuffle", description="랜덤 팀 생성")
    async def shuffle(self, context: Context) -> None:
        try:
            await self.handler.shuffle(context)
        except commands.CommandError as e:
            self.bot.logger.warning(e)

    @commands.hybrid_command(
        name="s",
        description="alias of /lol shuffle",
        aliases=["ㅅ", "셔", "셔플", "r", "random"],
    )
    async def alias_shuffle(self, context: Context) -> None:
        await self.shuffle(context)


async def setup(bot) -> None:
    await bot.add_cog(Team(bot))
