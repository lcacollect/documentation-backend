import datetime
from typing import Annotated, Optional

import strawberry
from aiocache import Cache, cached
from lcaconfig.context import get_session, get_user
from lcaconfig.exceptions import DatabaseItemNotFound
from lcaconfig.graphql.input_filters import filter_model_query
from sqlalchemy.orm import selectinload
from sqlmodel import select
from strawberry.types import Info

import models.commit as models_commit
import models.reporting_schema as models_schema
import models.repository as models_repository
import models.tag as models_tag
from core.validate import authenticate
from schema.inputs import TagFilters


@strawberry.type
class GraphQLTag:
    added: datetime.date
    author_id: str
    commit_id: str
    commit: Annotated["GraphQLCommit", strawberry.lazy("schema.commit")]
    id: str
    name: str

    @strawberry.field
    def short_id(self) -> str:  # pragma: no cover
        return self.id[:8] if self.id is not None else None


async def query_tags(info: Info, reporting_schema_id: str, filters: Optional[TagFilters] = None) -> list[GraphQLTag]:
    """Get all tags"""

    session = get_session(info)
    reporting_schema = await session.get(models_schema.ReportingSchema, reporting_schema_id)
    await authenticate(info, reporting_schema.project_id)

    query = select(models_tag.Tag)
    if tags_field := [field for field in info.selected_fields if field.name == "tags"]:
        if [field for field in tags_field[0].selections if field.name == "commit"]:
            query = query.options(selectinload(models_tag.Tag.commit))

    if filters:
        query = filter_model_query(models_tag.Tag, filters, query)

    tags = (await session.exec(query)).all()

    return tags


async def update_tag(info: Info, id: str, name: Optional[str] = None, commit_id: Optional[str] = None) -> GraphQLTag:
    """Change the name of the tag or move it to a different commit."""

    session = get_session(info)
    tag = await session.get(models_tag.Tag, id)
    if not tag:
        raise DatabaseItemNotFound(f"Could not find Tag with id: {id}.")

    await authenticate_tag(info, tag.commit_id)

    kwargs = {"name": name, "commit_id": commit_id}
    for key, value in kwargs.items():
        if value is not None:
            setattr(tag, key, value)

    session.add(tag)

    await session.commit()
    await session.refresh(tag)

    query = select(models_tag.Tag).where(models_tag.Tag.id == tag.id)
    await session.exec(query)
    return tag


async def create_tag(info: Info, name: str, commit_id: str) -> GraphQLTag:
    """Add a new tag."""

    commit = await authenticate_tag(info, commit_id)

    session = get_session(info)
    user = get_user(info)

    tag = models_tag.Tag(
        author_id=user.claims.get("oid"),
        added=datetime.datetime.now(),
        name=name,
        commit_id=commit_id,
        commit=commit,
    )

    session.add(tag)
    await session.commit()
    await session.refresh(tag)

    query = select(models_tag.Tag).where(models_tag.Tag.id == tag.id)

    if tags_field := [field for field in info.selected_fields if field.name == "createTag"]:
        if [field for field in tags_field[0].selections if field.name == "commit"]:
            query = query.options(selectinload(models_tag.Tag.commit))

    await session.exec(query)
    return tag


async def delete_tag(info: Info, id: str) -> str:
    """Delete a tag"""

    session = get_session(info)
    tag = await session.get(models_tag.Tag, id)

    await authenticate_tag(info, tag.commit_id)

    await session.delete(tag)
    await session.commit()
    return id


@cached(ttl=60, cache=Cache.MEMORY)
async def authenticate_tag(info: Info, commit_id: str) -> models_commit.Commit:
    """Authenticates whether user has access to the given tag"""

    session = get_session(info)
    commit_query = (
        select(models_commit.Commit)
        .where(models_commit.Commit.id == commit_id)
        .options(
            selectinload(models_commit.Commit.repository).options(
                selectinload(models_repository.Repository.reporting_schema)
            )
        )
    )
    commit = (await session.exec(commit_query)).one()
    await authenticate(info, commit.repository.reporting_schema.project_id)
    return commit
