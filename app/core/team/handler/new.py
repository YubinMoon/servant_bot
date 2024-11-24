from ....common.logger import get_logger
from ...database import get_session
from ...model.team import Member, Team
from ..controller import NewTeamController
from .base import BaseHandler

logger = get_logger(__name__)


class NewTeamHandler(BaseHandler):

    def __init__(self, controller: NewTeamController, team_name: str = "") -> None:
        super().__init__(None, controller.context, team_name)
        self.controller = controller
        self.team_name = team_name

    async def action(self):
        message_id = await self.controller.setup_embed(name=self.team_name)
        await self.create_tteam(message_id)
        logger.info(f"created new team: {self.team_name} ({message_id})")

    async def create_tteam(self, message_id):
        with get_session() as session:
            team = Team(name=self.team_name, message_id=message_id)
            session.add(team)
            session.commit()
