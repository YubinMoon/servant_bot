import json
import random
from datetime import datetime, timedelta

from sqlmodel import Session, select

from ....common.logger import get_logger
from ...error.team import TeamError
from ...model.team import Team, TeamHistory
from ..controller import ShuffleTeamController
from .base import BaseHandler

logger = get_logger(__name__)

MULTIPLE = 0.1
BASE_WEIGHT = [[10000.0 for _ in range(5)] for _ in range(5)]


async def get_random_team(db: Session, team: Team) -> list[int]:
    members = team.members
    if len(members) == 5:
        return await _shuffle_rank(db, team)
    elif len(members) == 10:
        return await shuffle_custom(team)
    else:
        raise TeamError(
            "Team member number is not correct.",
            f"**{team.name}** 팀에 참가한 맴버가 맞지 않아요.",
            "팀 인원을 5명 또는 10명으로 맞춰주세요.",
        )


async def _shuffle_rank(db: Session, team: Team) -> None:
    histories = db.exec(select(TeamHistory).where(TeamHistory.team == team)).all()
    rank_team = await _get_rank_team(histories)
    db.add(TeamHistory(team=team, numbers=json.dumps(rank_team)))
    db.commit()
    return rank_team


async def _get_rank_team(histories: list[TeamHistory]) -> list[int]:
    team = []
    weights = await _get_weight(histories)
    while len(set(team)) != 5:
        team.clear()
        for i in range(5):
            team.append(random.choices(range(5), weights=weights[i])[0])
    new_team = team.copy()
    for i, member in enumerate(team):
        new_team[member] = i
    return new_team


async def _get_weight(histories: list[TeamHistory]) -> list[list[float]]:
    weight = BASE_WEIGHT.copy()
    for history in histories:
        members: list[int] = json.loads(history.numbers)
        weight = _calc_weight(weight, members)
    return weight


def _calc_weight(weight: list[list[float]], record: list[int]) -> list[list[float]]:
    new_weight = weight.copy()
    for lane_no, member_no in enumerate(record):
        remain = (new_weight[member_no][lane_no] * (1 - MULTIPLE)) // 4
        for i in range(5):
            if i == lane_no:
                new_weight[member_no][i] -= remain * 4
            else:
                new_weight[member_no][i] += remain
    return new_weight


async def shuffle_custom(team: Team) -> list[int]:
    members = team.members.copy()
    return random.shuffle(members)


class ShuffleTeamHandler(BaseHandler):
    def __init__(self, db: Session, controller: ShuffleTeamController) -> None:
        super().__init__(db, controller)
        self.controller = controller

    async def run(self):
        teams = self.get_team_list()
        selected_team = await self.controller.get_team_from_view(teams)

        # # For Test
        # while len(selected_team.members) < 10:
        #     selected_team.members.append(
        #         Member(discord_id=1234, name=f"test{len(selected_team.members)}")
        #     )
        # self.db.add(selected_team)
        # self.db.commit()
        # self.db.refresh(selected_team)

        members = selected_team.members
        if len(members) == 5:
            await self.shuffle_rank(selected_team)
        elif len(members) == 10:
            await self.shuffle_custom(selected_team)
        else:
            raise TeamError(
                "Team member number is not correct.",
                f"**{selected_team.name}** 팀에 참가한 맴버가 맞지 않아요.",
                "팀 인원을 5명 또는 10명으로 맞춰주세요.",
            )

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

    async def shuffle_rank(self, team: Team) -> None:
        histories = self.db.exec(
            select(TeamHistory).where(TeamHistory.team == team)
        ).all()
        rank_team = await self.get_rank_team(histories)
        self.db.add(TeamHistory(team=team, numbers=json.dumps(rank_team)))
        self.db.commit()
        await self.controller.send_rank_team(team, rank_team)

    async def get_rank_team(self, histories: list[TeamHistory]) -> list[int]:
        team = []
        weights = await self.get_weight(histories)
        logger.info(weights)
        while len(set(team)) != 5:
            team.clear()
            for i in range(5):
                team.append(random.choices(range(5), weights=weights[i])[0])
        new_team = team.copy()
        for i, member in enumerate(team):
            new_team[member] = i
        return new_team

    async def get_weight(self, histories: list[TeamHistory]) -> list[list[float]]:
        weight = [[10000.0 for _ in range(5)] for _ in range(5)]
        for history in histories:
            members: list[int] = json.loads(history.numbers)
            weight = self.calc_weight(weight, members)
        return weight

    def calc_weight(
        self, weight: list[list[float]], record: list[int]
    ) -> list[list[float]]:
        new_weight = weight.copy()
        for lane_no, member_no in enumerate(record):
            remain = (new_weight[member_no][lane_no] * (1 - MULTIPLE)) // 4
            for i in range(5):
                if i == lane_no:
                    new_weight[member_no][i] -= remain * 4
                else:
                    new_weight[member_no][i] += remain
        return new_weight

    async def shuffle_custom(self, team: Team) -> None:
        members = team.members.copy()
        random.shuffle(members)
        await self.controller.send_custom_team(team, members)
