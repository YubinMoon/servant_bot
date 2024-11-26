from datetime import datetime, timedelta

from sqlmodel import Session, select

from ...error.team import TeamError
from ...model.team import Team
from ..controller import TeamInfoController
from .base import BaseHandler


class TeamInfoHandler(BaseHandler):
    def __init__(self, db: Session, controller: TeamInfoController) -> None:
        super().__init__(db, controller)
        self.controller = controller

    async def run(self):
        teams = self.get_team_list()
        selected_team = await self.controller.get_team_from_view(teams)
        await self.controller.send_team_info(selected_team)

    def get_team_list(self):
        teams = self.db.exec(
            select(Team)
            .where(Team.created_at > (datetime.now() - timedelta(days=1)))
            .order_by(Team.created_at.desc())
        ).all()
        if not teams:
            raise TeamError(
                "Team is not found.",
                f"현재 생성된 팀이 없어요.",
                "**/q**로 팀을 만들어 보세요.",
            )
        return teams
