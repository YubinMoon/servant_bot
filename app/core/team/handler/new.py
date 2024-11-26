from sqlmodel import Session

from ....common.logger import get_logger
from ...model.team import Team
from ..controller import NewTeamController
from .join import JoinTeamHandler

logger = get_logger(__name__)


async def create_team(db: Session, message_id: int, name: str) -> Team:
    team = Team(name=name, message_id=message_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


class NewTeamHandler(JoinTeamHandler):
    def __init__(
        self, db: Session, controller: NewTeamController, team_name: str = ""
    ) -> None:
        super().__init__(db, controller)
        self.controller = controller
        self.team_name = team_name

    async def run(self):
        message_id = await self.controller.setup_embed(name=self.team_name)
        team = await self.create_tteam(message_id)
        logger.info(f"created new team: {self.team_name} ({message_id})")
        await self.add_member(team)

    async def create_tteam(self, message_id) -> Team:
        team = Team(name=self.team_name, message_id=message_id)
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team
