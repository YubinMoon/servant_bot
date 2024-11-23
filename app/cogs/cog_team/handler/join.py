from datetime import datetime, timedelta

from sqlalchemy.orm import selectinload
from sqlmodel import select

from database import get_session
from error.team import AlreadyInTeamError, NoTeamError, NoTeamSelectError
from model.team import Member, Team
from utils.logger import get_logger

from ..controller import JoinTeamController
from .base import BaseHandler

logger = get_logger(__name__)


class JoinTeamHandler(BaseHandler):
    def __init__(self, controller: JoinTeamController) -> None:
        super().__init__(None, controller.context, "")
        self.controller = controller

    async def action(self) -> None:
        teams = self.get_team_list()
        selected_team = await self.controller.get_team_name_from_view(teams)
        if not selected_team:
            logger.warn("No team is selected.")
            return
        self.add_member(selected_team)
        updated_team = self.get_updated_team(selected_team)
        await self.controller.update_message(updated_team)

    def get_team_list(self):
        with get_session() as session:
            teams = session.exec(
                select(Team)
                .options(selectinload(Team.members))
                .where(Team.created_at > (datetime.now() - timedelta(days=1)))
            ).all()
        if not teams:
            raise NoTeamError("Team is not found.")
        return teams

    def add_member(self, team: Team):
        user_id = self.controller.user_id
        user_name = self.controller.user_name
        member_ids = [member.discord_id for member in team.members]

        # check duplication
        if self.controller.user_id in member_ids:
            raise AlreadyInTeamError(
                f"{user_name} (ID: {user_id}) tried to join a team {team.name} that the user is already in.",
                team.name,
            )

        # add member
        member = Member(discord_id=user_id, name=user_name, team_id=team.id)
        with get_session() as session:
            session.add(member)
            session.commit()
        logger.debug(
            f"{user_name} (ID: {user_id}) joined the team {team.name} (ID: {team.id})."
        )

    def get_updated_team(self, team: Team) -> Team:
        with get_session() as session:
            new_team = session.get(Team, team.id, options=[selectinload(Team.members)])
        return new_team
