import json
import random
from datetime import datetime, timedelta
from re import I

from sqlmodel import Session, select

from app.core import team

from ...common.logger import get_logger
from ..error.team import TeamError
from ..model.team import Member, Team, TeamHistory

logger = get_logger(__name__)


## new ###
async def create_team(db: Session, message_id: int, name: str) -> Team:
    team = Team(name=name, message_id=message_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


### join ###
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


### left ###
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


### shuffle ###
MULTIPLE = 0.1
BASE_WEIGHT = [[10000.0 for _ in range(5)] for _ in range(5)]


async def get_random_team(db: Session, team: Team) -> list[int]:
    members = team.members
    if len(members) == 1:
        raise TeamError(
            "Team has only one member.",
            "한명으로 팀을 어케 만듭니까?",
            "친구를 데려와 주세요.",
        )
    if len(members) == 5:
        return await _shuffle_rank(db, team)
    else:
        return await shuffle_custom(team)


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
    members = [i for i in range(len(team.members))]
    random.shuffle(members)
    return members


async def delete_team(db: Session, team: team):
    db.delete(team)
    db.commit()
