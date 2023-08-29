import datetime
from typing import TYPE_CHECKING, Annotated, Optional

import strawberry
from aiocache import cached
from lcacollect_config.context import get_session
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlalchemy.orm import selectinload
from sqlmodel import select
from strawberry.types import Info

import models.commit as models_commit
import models.reporting_schema as models_schema
import models.repository as models_repository
import models.schema_category as models_category
from core.validate import authenticate
from schema.inputs import CommitFilters

if TYPE_CHECKING:  # pragma: no cover
    from schema.schema_category import GraphQLSchemaCategory
    from schema.schema_element import GraphQLSchemaElement
    from schema.tag import GraphQLTag
    from schema.task import GraphQLTask


@strawberry.type
class GraphQLCommit:
    id: str
    added: datetime.date
    parent_id: str | None
    repository_id: str
    author_id: str | None
    reporting_schema_id: str
    schema_categories: list[Annotated["GraphQLSchemaCategory", strawberry.lazy("schema.schema_category")]] | None
    schema_elements: list[Annotated["GraphQLSchemaElement", strawberry.lazy("schema.schema_element")]] | None
    tasks: list[Annotated["GraphQLTask", strawberry.lazy("schema.task")]] | None
    tags: list[Annotated["GraphQLTag", strawberry.lazy("schema.tag")]] | None

    @strawberry.field
    def short_id(self) -> str:  # pragma: no cover
        return self.id[:8] if self.id is not None else None


async def query_commits(
    info: Info, reporting_schema_id: str, filters: Optional[CommitFilters] = None
) -> list[GraphQLCommit]:
    """Get all commits of a Reporting Schema"""

    session = get_session(info)

    await authenticate_commit(info, reporting_schema_id)

    repository = (
        await session.exec(
            select(models_repository.Repository).where(
                models_repository.Repository.reporting_schema_id == reporting_schema_id
            )
        )
    ).first()

    query = select(models_commit.Commit).where(models_commit.Commit.repository_id == repository.id)

    query = await graphql_options(info, query)
    if filters:
        query = filter_model_query(models_commit.Commit, filters, query)

    commits = await session.exec(query)
    return commits.all()


@cached(ttl=60)
async def authenticate_commit(info: Info, reporting_schema_id: str) -> models_schema.ReportingSchema:
    """Authenticates the user trying access a commit"""

    session = get_session(info)
    auth_query = select(models_schema.ReportingSchema).where(models_schema.ReportingSchema.id == reporting_schema_id)
    reporting_schema = (await session.exec(auth_query)).first()
    await authenticate(info, reporting_schema.project_id, check_public=True)
    return reporting_schema


async def graphql_options(info, query):
    """
    Optionally "select IN" loads the needed collections of a commit
    based on the request provided in the info

    Args:
        info (Info): request information
        query: current query provided

    Returns: updated query
    """
    if commit_field := [field for field in info.selected_fields if field.name == "commits"]:
        if category_field := [field for field in commit_field[0].selections if field.name == "categories"]:
            if [field for field in category_field[0].selections if field.name == "elements"]:
                query = query.options(
                    selectinload(models_commit.Commit.schema_categories).options(
                        selectinload(models_category.SchemaCategory.elements)
                    )
                )
            else:
                query = query.options(selectinload(models_commit.Commit.schema_categories))
        if [field for field in commit_field[0].selections if field.name == "elements"]:
            query = query.options(selectinload(models_commit.Commit.schema_elements))

        if [field for field in commit_field[0].selections if field.name == "tasks"]:
            query = query.options(selectinload(models_commit.Commit.tasks))

        if [field for field in commit_field[0].selections if field.name == "tags"]:
            query = query.options(selectinload(models_commit.Commit.tags))
    return query
