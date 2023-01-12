import datetime
from typing import Optional

from lcaconfig.formatting import string_uuid
from sqlmodel import Field, Relationship, SQLModel

from models.commit import Commit


class Tag(SQLModel, table=True):
    """Repository Tag database class"""

    added: datetime.date = Field(default_factory=datetime.datetime.now, nullable=False)
    author_id: str | None
    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)
    name: str = Field(nullable=False)

    # Relationships
    commit: Commit = Relationship(
        back_populates="tags",
    )
    commit_id: str = Field(foreign_key="commit.id", nullable=False)
