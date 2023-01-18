from typing import Optional

from lcacollect_config.formatting import string_uuid
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, SQLModel

from models.reporting_schema import ReportingSchema


class SchemaTemplate(SQLModel, table=True):
    """Reporting Schema Template class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)
    name: str | None

    # Relationships
    original_id: Optional[str] = Field(default=None, foreign_key="reportingschema.id")

    @property
    def original(self):
        if self.original_id and self.schemas:
            return [schema for schema in self.schemas if schema.id == self.original_id][0]

    schemas: list[ReportingSchema] = Relationship(
        back_populates="template",
        sa_relationship=RelationshipProperty(
            ReportingSchema,
            primaryjoin="foreign(SchemaTemplate.id) == ReportingSchema.template_id",
            uselist=True,
        ),
    )
