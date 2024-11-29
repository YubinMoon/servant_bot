from datetime import datetime, timedelta, timezone

from sqlmodel import Field, Relationship, SQLModel

UTC_9 = timezone(timedelta(hours=9))


class Target(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    discord_id: int
    guild_id: int
    channel_id: int

    states: list["TargetState"] = Relationship(
        back_populates="target", cascade_delete=True
    )


class TargetState(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC_9))
    end_time: datetime | None
    alerted: bool = False

    target_id: int = Field(foreign_key="target.id")
    target: Target = Relationship(back_populates="states")
