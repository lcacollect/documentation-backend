import json
from typing import Optional

from lcaconfig.formatting import string_uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, Relationship, SQLModel

from models.commit import Commit
from models.links import ElementCommitLink
from models.task import Task


class SchemaElement(SQLModel, table=True):
    """Schema Element database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)
    name: str
    quantity: float = Field(default=0.0)
    unit: str | None
    description: str | None
    result: dict = Field(default=None, sa_column=Column(JSON), nullable=False)

    # Relationships
    schema_category_id: str = Field(foreign_key="schemacategory.id")
    schema_category: "SchemaCategory" = Relationship(back_populates="elements")

    commits: Optional[list[Commit]] = Relationship(back_populates="schema_elements", link_model=ElementCommitLink)

    tasks: Optional[list[Task]] = Relationship(
        back_populates="element", sa_relationship_kwargs={"cascade": "all,delete"}
    )
    source_id: Optional[str] = Field(foreign_key="projectsource.id", nullable=True)
    source: Optional["ProjectSource"] = Relationship(back_populates="elements")
