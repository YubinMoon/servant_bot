import random
import discord
from discord.ext import commands
from discord.ext.commands import Context


class TeamHandler:
    LANE = ["탑", "정글", "미드", "원딜", "서폿"]

    def __init__(self, bot) -> None:
        self.bot = bot
        self.multiple = 0.1
        self.base_weight = [[10000 for _ in range(5)] for _ in range(5)]
        self.messages: dict[int, discord.Message] = {}
        self.teams: dict[int, list[discord.Member]] = {}
        self.weights: dict[int, list[list[int]]] = {}

    async def start_team(self, context: Context) -> None:
        embed = discord.Embed(
            title="새로운 팀이 생성되었습니다.",
            description="**/rank join** 명령어를 통해 등록해 주세요",
            color=0xBEBEFE,
        )
        embed.add_field(name="0/5", value="")
        message = await context.send(embed=embed)

        channel_id = message.channel.id
        self.messages[channel_id] = message
        self.teams[channel_id] = []
        self.weights[channel_id] = self.base_weight.copy()

        await self.join_team(context)

    async def join_team(self, context: Context) -> None:
        channel_id = context.channel.id
        member = context.author

        if channel_id not in self.teams:
            await self.no_team_error(context)
        if member in self.teams[channel_id]:
            await self.already_in_team_error(context)
        if len(self.teams[channel_id]) >= 5:
            await self.max_team_error(context)

        self.teams[channel_id].append(member)
        await self.update_message(channel_id)

        if len(self.teams[channel_id]) > 1:
            embed = discord.Embed(
                description=f"{member.mention}님이 팀에 등록되었습니다.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)

    async def update_message(self, channel_id: int) -> None:
        if channel_id not in self.messages:
            return
        message = self.messages[channel_id]
        embed = message.embeds[0]
        embed.set_field_at(
            index=0,
            name=f"{len(self.teams[channel_id])}/5",
            value=" - ".join([member.mention for member in self.teams[channel_id]]),
        )
        await message.edit(embed=embed)

    async def shuffle_team(self, context: Context) -> None:
        channel_id = context.channel.id

        if channel_id not in self.teams:
            await self.no_team_error(context)
        if len(self.teams[channel_id]) != 5:
            await self.team_member_num_error(context)

        team = self.get_rank_team(channel_id)
        self.adjustment_weight(channel_id, team)
        embed = discord.Embed(
            description="새로운 팀을 구성했습니다.",
            color=0xBEBEFE,
        )
        for i, lane in enumerate(self.LANE):
            member_no = team.index(i)
            member = self.teams[channel_id][member_no]
            embed.add_field(name=lane, value=member.mention)
        await context.send(embed=embed)

    def get_rank_team(self, channel_id: int) -> list[int]:
        team = []
        while len(set(team)) != 5:
            team.clear()
            for i in range(5):
                team.append(
                    random.choices(range(5), weights=self.weights[channel_id][i])[0]
                )
        return team

    def adjustment_weight(self, channel_id: int, team: list[int]) -> None:
        weight = self.weights[channel_id].copy()
        for member_no, lane_no in enumerate(team):
            remain = (weight[member_no][lane_no] * (1 - self.multiple)) // 4
            for i in range(5):
                if i == lane_no:
                    weight[member_no][i] -= remain * 4
                else:
                    weight[member_no][i] += remain
        self.weights[channel_id] = weight

    async def no_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            title="팀이 생성되지 않았습니다.",
            description="**/rank start** 팀을 생성해 주세요.",
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

    async def max_team_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="팀이 꽉 찼습니다.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True)
        raise commands.CommandError("max rank team")

    async def team_member_num_error(self, context: Context) -> None:
        embed = discord.Embed(
            description="인원이 맞지 않습니다.",
            color=0xE02B2B,
        )
        await context.send(embed=embed, ephemeral=True)
        raise commands.CommandError("team member num error")


class Team(commands.Cog, name="team"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.handler = TeamHandler(bot)

    @commands.hybrid_group(
        name="rank",
        description="get rank lane at voice channel.",
    )
    async def rank(self, context: Context) -> None:
        pass

    @rank.command(name="start", description="start rank team.")
    async def rank_start(self, context: Context) -> None:
        try:
            await self.handler.start_team(context)
        except commands.CommandError as e:
            self.bot.logger.warning(e)

    @commands.hybrid_command(
        name="q", description="alias of /rank start", aliases=["ㅋ", "큐"]
    )
    async def alias_rank_start(self, context: Context) -> None:
        await self.rank_start(context)

    @rank.command(name="join", description="join rank team.")
    async def rank_join(self, context: Context) -> None:
        try:
            await self.handler.join_team(context)
        except commands.CommandError as e:
            self.bot.logger.warning(e)

    @commands.hybrid_command(
        name="j", description="alias of /rank join", aliases=["ㅊ", "참", "참여", "참가"]
    )
    async def alias_rank_join(self, context: Context) -> None:
        await self.rank_join(context)

    @rank.command(name="shuffle", description="generate new rank team.")
    async def rank_shuffle(self, context: Context) -> None:
        try:
            await self.handler.shuffle_team(context)
        except commands.CommandError as e:
            self.bot.logger.warning(e)

    @commands.hybrid_command(
        name="s",
        description="alias of /rank shuffle",
        aliases=["ㅅ", "셔", "셔플", "r", "random"],
    )
    async def alias_rank_shuffle(self, context: Context) -> None:
        await self.rank_shuffle(context)


async def setup(bot) -> None:
    await bot.add_cog(Team(bot))
