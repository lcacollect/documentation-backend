from typing import Optional

from lcacollect_config.formatting import string_uuid
from sqlmodel import Field, Relationship, SQLModel

from models.commit import Commit
from models.links import CategoryCommitLink
from models.schema_element import SchemaElement
from models.task import Task


class SchemaCategory(SQLModel, table=True):
    """Schema Category database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)
    path: str | None
    name: str | None
    description: str | None

    # Relationships
    reporting_schema_id: Optional[str] = Field(foreign_key="reportingschema.id")
    reporting_schema: "ReportingSchema" = Relationship(back_populates="categories")
    elements: list[SchemaElement] = Relationship(
        back_populates="schema_category",
        sa_relationship_kwargs={"cascade": "all,delete"},
    )
    commits: list[Commit] = Relationship(back_populates="schema_categories", link_model=CategoryCommitLink)
    tasks: list[Task] = Relationship(back_populates="category", sa_relationship_kwargs={"cascade": "all,delete"})
