from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    message_id: int
    members: list["Member"] = Relationship(back_populates="team", cascade_delete=True)
    always_active: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class Member(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    discord_id: int
    name: str

    team_id: int = Field(foreign_key="team.id")
    team: Team = Relationship(back_populates="members")
