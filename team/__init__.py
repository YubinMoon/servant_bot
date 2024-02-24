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
            title="새로운 팀이 구성되었어요.",
            description="**/j**로 등록... 하든가 말든가",
            color=0xBEBEFE,
        )
        embed.add_field(name="0/5", value="")
        embed.set_footer(text="/s로 굴릴 수 있어요. /c로 팀 등록을 취소할 수 있어요.")
        message = await context.send(embed=embed, silent=True)
        try:
            await self.db.start_team(channel_id, message.id)
            await self.join(context)
        except Exception as e:
            self.logger.error(e)
            embed = discord.Embed(
                title="팀 생성에 실패했어요.",
                description="조금 쉬어야 할 것 같아요.",
                color=0xE02B2B,
            )
            await message.edit(embed=embed)

            error_embed = discord.Embed(
                title="ERROR LOG",
                description=f"```{traceback.format_exc()}```",
                color=0xE02B2B,
            )
            await context.send(embed=error_embed, ephemeral=True, silent=True)
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
            description=f"{member.mention}님이 팀에 참가했어요.",
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
            description=f"{member.mention}님이 팀 등록을 취소했어요.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed, silent=True)

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
            description="라인을 배정했어요.",
            color=0xBEBEFE,
        )
        for i, lane in enumerate(self.LANE):
            member_no = team.index(i)
            member = members[member_no]
            embed.add_field(
                name=lane,
                value=f"{member.mention} ({member.global_name})",
                inline=False,
            )
        await context.send(embed=embed)

    async def shuffle_custom(self, context: Context) -> None:
        channel_id = context.channel.id

        members = await self.db.get_members(channel_id)
        random.shuffle(members)
        embed = discord.Embed(
            description="새로운 대전을 구성했어요.",
            color=0xBEBEFE,
        )
        embed.add_field(
            name="1팀",
            value="\n".join(
                [f"{member.mention} ({member.global_name})" for member in members[:5]]
            ),
            inline=False,
        )
        embed.add_field(
            name="2팀",
            value="\n".join(
                [f"{member.mention} ({member.global_name})" for member in members[5:]]
            ),
            inline=False,
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

    async def info(self, context: Context) -> None:
        channel_id = context.channel.id
        if await self.db.get_team(channel_id) is None:
            await self.no_team_error(context)
        members = await self.db.get_members(channel_id)
        embed = discord.Embed(
            color=0xBEBEFE,
        )
        embed.add_field(
            name="현재 팀원",
            value="\n".join(
                [f"{member.mention} ({member.name})" for member in members]
            ),
        )
        await context.send(embed=embed, ephemeral=True, silent=True)

    async def no_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            title="팀이 생성되지 않았어요.",
            description="**/q**로 팀을 먼저 생성해 주세요.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True, silent=True)
        raise commands.CommandError("no rank team")

    async def already_in_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="이미 팀에 등록되어있어요.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True, silent=True)
        raise commands.CommandError("already in rank team")

    async def already_not_in_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="팀에 등록되어 있지 않아요.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True, silent=True)
        raise commands.CommandError("already not in rank team")

    async def max_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="팀이 꽉 찼어요.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True, silent=True)
        raise commands.CommandError("max rank team")

    async def team_member_num_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="인원이 맞지 않습니다.\n\n5명 또는 10명이어야 합니다.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True, slient=True)
        raise commands.CommandError("team member num error")
