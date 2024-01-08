import random
import discord
from discord.ext import commands
from discord.ext.commands import Context


class Team(commands.Cog, name="team"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.base_weight = [[100 for _ in range(5)] for _ in range(5)]
        self.rank_member_list = []
        self.rank_history = []

    def get_rank_team(self) -> list[int]:
        # 가중치 설정
        self.rank_history[::-1]  # 최근 기록부터
        for team in self.rank_history:
            for member_no, lane_no in enumerate(team):  # 각 기록의 사람 마다
                tmp = self.base_weight[member_no][lane_no] // 5
                remain = self.base_weight[member_no][lane_no] % 5
                for i in range(5):
                    if i == lane_no:
                        self.base_weight[member_no][i] = tmp + remain
                    else:
                        self.base_weight[member_no][i] += tmp
        # 팀 뽑기
        team = []
        while len(set(team)) != 5:
            team.clear()
            for i in range(5):
                team.append(
                    random.choices(range(5), weights=self.base_weight[i], k=1)[0]
                )
        return team

    def shuffle_rank_team(
        self, member_list: list[discord.Member]
    ) -> dict[str, discord.Member]:
        team_base = self.get_rank_team()
        self.rank_history.append(team_base)
        team = {}
        for i, t in enumerate(team_base):
            if t == 0:
                team["탑"] = member_list[i]
            elif t == 1:
                team["정글"] = member_list[i]
            elif t == 2:
                team["미드"] = member_list[i]
            elif t == 3:
                team["원딜"] = member_list[i]
            elif t == 4:
                team["서폿"] = member_list[i]
        return team

    @commands.hybrid_group(
        name="rank",
        description="get rank lane at voice channel.",
    )
    async def rank(self, context: Context) -> None:
        pass

    @rank.command(name="shuffle", description="generate new rank team.")
    async def rank_base(self, context: Context) -> None:
        if context.author.voice is None:
            embed = discord.Embed(description="음성 채널에 접속해주세요.", color=0xBEBEFE)
            await context.send(embed=embed, ephemeral=True)
            return

        member_list = context.author.voice.channel.members
        member_list = member_list * 5
        if len(member_list) == 5:
            if not self.rank_member_list:
                self.rank_member_list = member_list.copy()
            else:
                embed = discord.Embed(description="팀을 구성한 인원이 변경되었습니다.", color=0xBEBEFE)
                embed.set_footer(text="팀을 초기화 해주세요.")
                await context.send(embed=embed, ephemeral=True)
                return
            if self.rank_member_list == member_list:
                team = self.shuffle_rank_team(member_list)
                embed = discord.Embed(description="새로운 팀을 구성했습니다.", color=0xBEBEFE)
                embed.add_field(name="탑", value=team["탑"].mention, inline=False)
                embed.add_field(name="정글", value=team["정글"].mention, inline=False)
                embed.add_field(name="미드", value=team["미드"].mention, inline=False)
                embed.add_field(name="원딜", value=team["원딜"].mention, inline=False)
                embed.add_field(name="서폿", value=team["서폿"].mention, inline=False)
                await context.send(embed=embed)
            return
        elif len(member_list) < 5:
            embed = discord.Embed(description="팀을 구성할 인원이 부족합니다.", color=0xBEBEFE)
            embed.add_field(name="현재 인원", value=len(member_list))
            embed.set_footer(text="채널에 5명만 있어야 합니다.")
            await context.send(embed=embed, ephemeral=True)
            return
        else:
            embed = discord.Embed(description="팀을 구성할 인원이 많습니다.", color=0xBEBEFE)
            embed.add_field(name="현재 인원", value=len(member_list))
            embed.set_footer(text="채널에 5명만 있어야 합니다.")
            await context.send(embed=embed, ephemeral=True)
            return

    @rank.command(name="clear", description="clear rank history.")
    async def rank_clear(self, context: Context) -> None:
        self.rank_history.clear()
        self.base_weight = [[100 for _ in range(5)] for _ in range(5)]
        embed = discord.Embed(description="팀 기록을 초기화했습니다.", color=0xBEBEFE)
        await context.send(embed=embed, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(Team(bot))
