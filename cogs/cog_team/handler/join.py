from typing import TYPE_CHECKING

from discord import Embed, NotFound

from error.team import AlreadyInTeamError, NoTeamError, NoTeamMessageError
from utils import color

from .base import BaseHandler

if TYPE_CHECKING:
    from discord import Message
    from discord.ext.commands import Context

    from bot import ServantBot


class JoinTeamHandler(BaseHandler):
    logger_name = "join_team_handler"

    def __init__(
        self, bot: "ServantBot", context: "Context", team_name: str = ""
    ) -> None:
        super().__init__(bot, context, team_name)

    async def action(self) -> None:
        # await self.check_members()
        await self.db.add_member(self.author)
        await self.update_message()
        self.logger.info(
            f"{self.author} (ID: {self.author.id}) joined the team {self.team_name}."
        )

    async def check_members(self):
        members = await self.db.get_members()
        if self.author.id in members:
            raise AlreadyInTeamError(
                f"{self.author} (ID: {self.author.id}) tried to join a team {self.team_name} that the user is already in.",
                self.team_name,
            )

    async def update_message(self) -> None:
        message = await self.get_message()
        await self.refresh_message(message)
        await self.notify(message)

    async def get_message(self):
        message_id = await self.db.get_message_id()
        if message_id is None:
            raise NoTeamError("Team is not found.", self.team_name)

        try:
            message = await self.channel.fetch_message(message_id)
        except NotFound as e:
            raise NoTeamMessageError(
                "Team Create message is not found.", self.team_name
            )
        return message

    async def refresh_message(self, message: "Message") -> None:
        members = await self.db.get_members()
        if message.embeds == []:
            raise NoTeamMessageError("Team Create embed is not found.", self.team_name)
        embed = message.embeds[0]
        embed.set_field_at(
            index=0,
            name=f"현제 인원: {len(members)}",
            value=" - ".join([f"<@{member_id}>" for member_id in members]),
        )
        await message.edit(embed=embed)

    async def notify(self, message: "Message"):
        embed = Embed(
            description=f"{self.author.mention}님이 **{self.team_name}**팀에 참가했어요. {message.jump_url}",
            color=color.BASE,
        )
        await self.context.send(embed=embed)
