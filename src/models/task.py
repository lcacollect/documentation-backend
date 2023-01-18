import datetime
from enum import Enum
from typing import Optional

from lcacollect_config.formatting import string_uuid
from sqlmodel import Field, Relationship, SQLModel

from models.comment import Comment
from models.commit import Commit
from models.links import TaskCommitLink


class Task(SQLModel, table=True):
    """Task database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)
    due_date: Optional[datetime.date] = Field(default_factory=datetime.date.today, nullable=False)
    name: str
    description: str
    status: str | None

    # Relationships
    reporting_schema_id: Optional[str] = Field(foreign_key="reportingschema.id")
    reporting_schema: "ReportingSchema" = Relationship(back_populates="tasks")

    category_id: Optional[str] = Field(foreign_key="schemacategory.id")
    category: "SchemaCategory" = Relationship(back_populates="tasks")

    element_id: Optional[str] = Field(foreign_key="schemaelement.id")
    element: "SchemaElement" = Relationship(back_populates="tasks")

    commits: list[Commit] = Relationship(back_populates="tasks", link_model=TaskCommitLink)
    comments: list[Comment] = Relationship(back_populates="task")
    author_id: str | None
    assignee_id: str | None
    assigned_group_id: str | None
