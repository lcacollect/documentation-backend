import datetime
from typing import TYPE_CHECKING, Optional

from lcacollect_config.formatting import string_uuid
from sqlmodel import Field, Relationship, SQLModel

from models.links import CategoryCommitLink, ElementCommitLink, TaskCommitLink

if TYPE_CHECKING:
    from models.repository import Repository
    from models.schema_category import SchemaCategory
    from models.schema_element import SchemaElement
    from models.tag import Tag
    from models.task import Task


class Commit(SQLModel, table=True):
    """Repository Commit database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, nullable=False)
    added: datetime.date = Field(default_factory=datetime.datetime.now, nullable=False)
    short_id: str | None

    # Relationships
    parent_id: Optional[str] = Field(default=None, nullable=True, foreign_key="commit.id")
    parent: Optional["Commit"] = Relationship(
        back_populates="child", sa_relationship_kwargs={"uselist": False, "remote_side": "Commit.id"}
    )
    child: "Commit" = Relationship(back_populates="parent")

    repository_id: str = Field(foreign_key="repository.id")
    repository: "Repository" = Relationship(back_populates="commits")
    author_id: str | None

    schema_categories: list["SchemaCategory"] = Relationship(back_populates="commits", link_model=CategoryCommitLink)
    schema_elements: list["SchemaElement"] = Relationship(back_populates="commits", link_model=ElementCommitLink)
    tasks: list["Task"] = Relationship(back_populates="commits", link_model=TaskCommitLink)
    tags: list["Tag"] = Relationship(back_populates="commit", sa_relationship_kwargs={"cascade": "all,delete"})

    @classmethod
    def copy_from_parent(cls, previous_commit: "Commit", author_id: str) -> "Commit":
        return cls(
            parent_id=previous_commit.id,
            added=datetime.date,
            repository_id=previous_commit.repository_id,
            schema_categories=previous_commit.schema_categories,
            schema_elements=previous_commit.schema_elements,
            repository=previous_commit.repository,
            author_id=author_id,
            tasks=previous_commit.tasks,
        )
