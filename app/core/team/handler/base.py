from sqlmodel import Session

from ..controller import BaseTeamController


class BaseHandler:
    def __init__(
        self,
        db: Session,
        controller: BaseTeamController,
    ) -> None:
        self.db = db
        self.controller = controller

    async def run(self) -> None:
        raise NotImplementedError
