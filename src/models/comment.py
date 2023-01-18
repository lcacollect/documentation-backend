import datetime
from typing import Optional

from lcacollect_config.formatting import string_uuid
from sqlmodel import Field, Relationship, SQLModel


class Comment(SQLModel, table=True):
    """Task database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)
    added: datetime.date = Field(default_factory=datetime.datetime.now, nullable=False)
    text: str

    # Relationships
    task: "Task" = Relationship(back_populates="comments")
    task_id: Optional[str] = Field(foreign_key="task.id")
    author_id: str | None
