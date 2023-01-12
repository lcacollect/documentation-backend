from typing import Optional

from sqlmodel import Field, SQLModel


class CategoryCommitLink(SQLModel, table=True):
    """Category Commit Database class"""

    schema_category_id: Optional[str] = Field(default=None, foreign_key="schemacategory.id", primary_key=True)
    commit_id: Optional[str] = Field(default=None, foreign_key="commit.id", primary_key=True)


class ElementCommitLink(SQLModel, table=True):
    """Element Commit Database class"""

    schema_element_id: Optional[str] = Field(default=None, foreign_key="schemaelement.id", primary_key=True)
    commit_id: Optional[str] = Field(default=None, foreign_key="commit.id", primary_key=True)


class TaskCommitLink(SQLModel, table=True):
    """Task Commit Database class"""

    task_id: Optional[str] = Field(default=None, foreign_key="task.id", primary_key=True)
    commit_id: Optional[str] = Field(default=None, foreign_key="commit.id", primary_key=True)
