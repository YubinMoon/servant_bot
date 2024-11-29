from datetime import datetime, timedelta

from sqlmodel import Session, select

from ....common.logger import get_logger
from ...error.team import TeamError
from ...model.team import Member, Team
from ..controller import JoinTeamController
from .base import BaseHandler

logger = get_logger(__name__)


def get_team_list(db: Session):
    teams = db.exec(
        select(Team)
        .where(Team.created_at > (datetime.now() - timedelta(days=1)))
        .order_by(Team.created_at.desc())
    ).all()
    if not teams:
        raise TeamError(
            "Team is not found.",
            "팀을 찾을 수 없어요.",
            "**/q**로 팀을 새로 생성해 보세요.",
        )
    return teams


async def add_member(db: Session, team: Team, user_id: int, user_name: str):
    member_ids = [member.discord_id for member in team.members]

    # check duplication
    if user_id in member_ids:
        raise TeamError(
            f"Already in the team {team.name}.",
            f"이미 **{team.name}** 팀에 참가하고 있어요.",
            "팀을 떠나려면 **/c**로 취소해 주세요.",
        )

    # add member
    member = Member(discord_id=user_id, name=user_name, team_id=team.id)
    db.add(member)
    db.commit()
    db.refresh(team)


class JoinTeamHandler(BaseHandler):
    def __init__(self, db: Session, controller: JoinTeamController) -> None:
        super().__init__(db, controller)
        self.controller = controller

    async def run(self) -> None:
        teams = self.get_team_list()
        selected_team = await self.controller.get_team_from_view(teams)
        if not selected_team:
            raise TeamError("Team is not selected.", alert=False)
        await self.add_member(selected_team)

    def get_team_list(self):
        teams = self.db.exec(
            select(Team)
            .where(Team.created_at > (datetime.now() - timedelta(days=1)))
            .order_by(Team.created_at.desc())
        ).all()
        if not teams:
            raise TeamError(
                "Team is not found.",
                "팀을 찾을 수 없어요.",
                "**/q**로 팀을 새로 생성해 보세요.",
            )
        return teams

    async def add_member(self, team: Team):
        user_id = self.controller.user_id
        user_name = self.controller.user_name
        member_ids = [member.discord_id for member in team.members]

        # check duplication
        if self.controller.user_id in member_ids:
            raise TeamError(
                f"Already in the team {team.name}.",
                f"이미 **{team.name}** 팀에 참가하고 있어요.",
                "팀을 떠나려면 **/c**로 취소해 주세요.",
            )

        # add member
        member = Member(discord_id=user_id, name=user_name, team_id=team.id)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(team)

        await self.controller.update_message(team)
        logger.info(
            f"{user_name} (ID: {user_id}) joined the team {team.name} (ID: {team.id})."
        )
