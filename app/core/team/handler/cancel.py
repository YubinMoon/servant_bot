from datetime import datetime, timedelta

from httpx import delete
from sqlmodel import Session, select

from ....common.logger import get_logger
from ...error.team import TeamError
from ...model.team import Member, Team
from ..controller import CancelTeamController
from .join import JoinTeamHandler

logger = get_logger(__name__)


async def remove_member(db: Session, team: Team, user_id: int, user_name: str):
    member_ids = [member.discord_id for member in team.members]

    # check duplication
    if user_id not in member_ids:
        raise TeamError(
            f"Already left the team {team.name}.",
            f"**{team.name}** 팀에 참가하지 않았어요.",
            "팀에 참가하려면 **/j**로 참가해 주세요.",
        )

    # delete member
    member = db.exec(
        select(Member).where(Member.team == team, Member.discord_id == user_id)
    ).first()
    db.delete(member)
    db.commit()
    db.refresh(team)


class CancelTeamHandler(JoinTeamHandler):
    logger_name = "cancel_team_handler"

    def __init__(self, db: Session, controller: CancelTeamController) -> None:
        super().__init__(db, controller)
        self.controller = controller

    async def run(self):
        teams = self.get_team_list()
        selected_team = await self.controller.get_team_from_view(teams)
        if not selected_team:
            raise TeamError("Team is not selected.", alert=False)
        await self.delete_member(selected_team)

    def get_team_list(self):
        teams = self.db.exec(
            select(Team)
            .where(Team.created_at > (datetime.now() - timedelta(days=1)))
            .order_by(Team.created_at.desc())
        ).all()
        if not teams:
            raise TeamError(
                "Team is not found.",
                f"현재 참가한 팀이 없어요.",
                "**/j**로 팀에 참가해 보세요.",
            )
        return teams

    async def delete_member(self, team: Team):
        user_id = self.controller.user_id
        user_name = self.controller.user_name
        member_ids = [member.discord_id for member in team.members]

        if self.controller.user_id not in member_ids:
            raise TeamError(
                f"Already out of the team {team.name}.",
                f"**{team.name}** 팀에 참가하지 않았어요.",
                "팀에 참가하려면 **/j**로 참가해 주세요.",
            )

        team.members = [
            member for member in team.members if member.discord_id != user_id
        ]
        self.db.commit()
        await self.controller.update_message(team)
        logger.info(
            f"{user_name} (ID: {user_id}) joined the team {team.name} (ID: {team.id})."
        )
