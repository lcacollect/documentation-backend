import datetime
from typing import TYPE_CHECKING, Annotated, Optional

import strawberry
from aiocache import Cache, cached
from lcaconfig.context import get_session, get_user
from lcaconfig.exceptions import DatabaseItemNotFound
from lcaconfig.graphql.input_filters import filter_model_query
from sqlalchemy.orm import selectinload
from sqlmodel import select
from strawberry.types import Info

import models.comment as models_comment
import models.task as models_task
from core.validate import authenticate
from schema.inputs import CommentFilters

if TYPE_CHECKING:  # pragma: no cover
    from schema.task import GraphQLTask


@strawberry.federation.type(keys=["id"])
class GraphQLComment:
    id: strawberry.ID
    added: datetime.datetime
    text: str
    author_id: str = strawberry.federation.field(shareable=True)
    task_id = str
    task: Annotated["GraphQLTask", strawberry.lazy("schema.task")]


async def query_comments(info: Info, task_id: str, filters: Optional[CommentFilters] = None) -> list[GraphQLComment]:
    """Query all comments of a task"""

    query = select(models_comment.Comment)
    if task_id:
        await authenticate_comment(info, task_id)
        query = query.where(models_comment.Comment.task_id == task_id)
    if [field for field in info.selected_fields if field.name == "task"]:
        query = query.options(selectinload(models_comment.Comment.task))

    if filters:
        query = filter_model_query(models_comment.Comment, filters, query)

    session = get_session(info)
    comments = await session.exec(query)
    return comments.all()


async def add_comment_mutation(info: Info, task_id: str, text: str) -> GraphQLComment:

    """Add a comment to a task"""

    task = await authenticate_comment(info, task_id)

    session = get_session(info)
    user = get_user(info)

    # creates a task database class
    comment = models_comment.Comment(
        added=datetime.datetime.now(),
        text=text,
        task=task,
        task_id=task_id,
        author_id=user.claims.get("oid"),
    )

    session.add(comment)
    await session.commit()
    await session.refresh(comment)

    return comment


async def update_comment_mutation(info: Info, id: str, text: str) -> GraphQLComment:

    """Update a task comment"""

    session = get_session(info)
    comment = await session.get(models_comment.Comment, id)
    if not comment:
        raise DatabaseItemNotFound(f"Could not find Comment with id: {id}")
    await authenticate_comment(info, comment.task_id)

    kwargs = {"text": text}
    for key, value in kwargs.items():
        if value:
            setattr(comment, key, value)

    session.add(comment)

    await session.commit()
    await session.refresh(comment)

    query = (
        select(models_task.Comment)
        .where(models_comment.Comment.id == comment.id)
        .options(selectinload(models_comment.Comment.task))
    )
    await session.exec(query)
    return comment


async def delete_comment_mutation(info: Info, id: str) -> str:
    """Delete a comment"""

    session = get_session(info)
    comment = await session.get(models_comment.Comment, id)
    await authenticate_comment(info, comment.task_id)

    await session.delete(comment)
    await session.commit()
    return id


@cached(ttl=60, key_builder=lambda function, *args, **kwargs: f"{function.__name__}_{args[1]}")
async def authenticate_comment(info: Info, task_id: str) -> models_task.Task:

    """Authenticates the user trying to access a comment"""

    session = get_session(info)
    auth_query = (
        select(models_task.Task)
        .where(models_task.Task.id == task_id)
        .options(selectinload(models_task.Task.reporting_schema))
    )
    task = (await session.exec(auth_query)).one()
    await authenticate(info, task.reporting_schema.project_id)
    return task
