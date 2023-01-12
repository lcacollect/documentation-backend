from typing import Optional

from lcaconfig.formatting import string_uuid
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, SQLModel

from models.repository import Repository
from models.schema_category import SchemaCategory
from models.task import Task


class ReportingSchema(SQLModel, table=True):
    """Reporting Schema database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)
    name: str
    project_id: str | None

    # Relationships
    template_id: Optional[str] = Field()
    template: "SchemaTemplate" = Relationship(
        back_populates="schemas",
        sa_relationship=RelationshipProperty(
            "SchemaTemplate",
            primaryjoin="foreign(ReportingSchema.template_id) == SchemaTemplate.id",
            uselist=False,
        ),
    )
    repository: "Repository" = Relationship(
        back_populates="reporting_schema",
        sa_relationship_kwargs={"cascade": "all,delete"},
    )
    tasks: list[Task] = Relationship(
        back_populates="reporting_schema",
        sa_relationship_kwargs={"cascade": "all,delete"},
    )
    categories: list[SchemaCategory] = Relationship(
        back_populates="reporting_schema",
        sa_relationship_kwargs={"cascade": "all,delete"},
    )
