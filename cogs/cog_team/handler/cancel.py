from typing import TYPE_CHECKING

from discord import Embed

from utils import color

from .error import AlreadyOutTeamError
from .join import JoinTeamHandler

if TYPE_CHECKING:
    from discord import Message
    from discord.ext.commands import Context

    from bot import ServantBot


class CancelTeamHandler(JoinTeamHandler):
    logger_name = "cancel_team_handler"

    def __init__(
        self, bot: "ServantBot", context: "Context", team_name: str = ""
    ) -> None:
        super().__init__(bot, context, team_name)

    async def action(self):
        index = await self.get_member_index()
        await self.db.pop_member(self.guild.name, self.team_name, index)
        await self.update_message()
        self.logger.info(
            f"{self.author} (ID: {self.author.id}) cancel joining the team {self.team_name}."
        )

    async def get_member_index(self):
        members_id = await self.get_members_id()
        index = members_id.index(self.author.id)
        return index

    async def get_members_id(self):
        members_id = await self.db.get_members(self.guild.name, self.team_name)
        if self.author.id not in members_id:
            raise AlreadyOutTeamError(
                f"{self.author} (ID: {self.author.id}) tried to cancel joining a team that the user is not in.",
                self.team_name,
            )
        return members_id

    async def notify(self, message: "Message"):
        embed = Embed(
            description=f"{self.author.mention}님이 **{self.team_name}**팀 등록을 취소했어요.  {message.jump_url}",
            color=color.BASE,
        )
        await self.context.send(embed=embed, silent=True)
