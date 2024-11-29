from datetime import datetime

from sqlmodel import Session, select

from ...common.logger import get_logger
from ..model.monitor import UTC_9, Target, TargetState

logger = get_logger(__name__)


def set_target(
    db: Session, user_id: int, user_name: str, guild_id: int, channel_id: int
) -> Target:
    target = db.exec(
        select(Target).where(Target.discord_id == user_id, Target.guild_id == guild_id)
    ).first()
    if target:
        target.name = user_name
        target.channel_id = channel_id
    else:
        target = Target(
            name=user_name,
            discord_id=user_id,
            guild_id=guild_id,
            channel_id=channel_id,
        )
        db.add(target)
    db.commit()
    db.refresh(target)
    return target


def get_targets(db: Session, user_id: int, guild_id: int):
    targets = db.exec(
        select(Target).where(Target.discord_id == user_id, Target.guild_id == guild_id)
    ).first()
    return targets


def arrest_online(db: Session, target: Target):
    state = TargetState(target_id=target.id)
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def arrest_offline(db: Session, target: Target):
    state = db.exec(
        select(TargetState).where(
            TargetState.target_id == target.id, TargetState.end_time == None
        )
    ).first()
    if not state:
        return None
    state.end_time = datetime.now(UTC_9)
    db.commit()
    db.refresh(state)
    return state


def get_open_state(db: Session, target: Target):
    state = db.exec(
        select(TargetState).where(
            TargetState.target_id == target.id, TargetState.end_time == None
        )
    ).first()
    return state


def set_alerted(db: Session, state: TargetState):
    state.alerted = True
    db.commit()
    db.refresh(state)
    return state
