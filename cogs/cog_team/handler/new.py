from database import get_session
from model.team import Member, Team
from utils.logger import get_logger

from ..controller import NewTeamController
from .base import BaseHandler

logger = get_logger(__name__)


class NewTeamHandler(BaseHandler):
    logger_name = "new_team_handler"

    def __init__(self, controller: NewTeamController, team_name: str = "") -> None:
        self.controller = controller
        super().__init__(None, controller.context, team_name)

    async def action(self):
        message_id = await self.controller.setup_embed(name=self.team_name)
        await self.create_tteam(message_id)
        logger.info(f"created new team: {self.team_name} ({message_id})")

    async def create_tteam(self, message_id):
        with get_session() as session:
            team = Team(name=self.team_name, message_id=message_id)
            session.add(team)
            session.commit()
