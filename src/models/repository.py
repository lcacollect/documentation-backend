from typing import Optional

from lcaconfig.formatting import string_uuid
from sqlmodel import Field, Relationship, SQLModel

from models.commit import Commit


class Repository(SQLModel, table=True):
    """Repository database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)

    # Relationships
    reporting_schema_id: Optional[str] = Field(foreign_key="reportingschema.id")
    reporting_schema: "ReportingSchema" = Relationship(back_populates="repository")
    commits: list["Commit"] = Relationship(back_populates="repository")

    @property
    def head(self):
        return self.commits[-1]
