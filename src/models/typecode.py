from typing import Optional

from lcacollect_config.formatting import string_uuid
from sqlmodel import Field, Relationship, SQLModel


class TypeCodeElement(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, index=True)
    code: str
    name: str
    level: int
    parent_path: str = "/"

    # Relationships
    typecode_id: Optional[str] = Field(foreign_key="typecode.id")
    typecode: "TypeCode" = Relationship(back_populates="elements")

    categories: list["SchemaCategory"] = Relationship(
        back_populates="type_code_element",
        sa_relationship_kwargs={"cascade": "all,delete"},
    )


class TypeCode(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, index=True)
    name: str
    project_id: str | None
    domain: str | None

    # Relationships
    elements: list[TypeCodeElement] = Relationship(
        back_populates="typecode", sa_relationship_kwargs={"cascade": "all,delete"}
    )
