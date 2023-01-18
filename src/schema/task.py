import datetime
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Optional, Union

import strawberry
from lcacollect_config.context import get_session, get_user
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlalchemy.orm import selectinload
from sqlmodel import select
from strawberry.types import Info

import models.commit as models_commit
import models.reporting_schema as models_schema
import models.repository as models_repository
import models.schema_category as models_category
import models.schema_element as models_element
import models.task as models_task
from core.validate import authenticate, authenticate_group
from schema.inputs import TaskFilters
from schema.schema_category import GraphQLSchemaCategory
from schema.schema_element import GraphQLSchemaElement

if TYPE_CHECKING:  # pragma: no cover
    from schema.comment import GraphQLComment
    from schema.commit import GraphQLCommit
    from schema.reporting_schema import GraphQLReportingSchema


@strawberry.enum
class TaskItemType(Enum):
    Category = "Category"
    Element = "Element"


@strawberry.enum
class TaskStatus(Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    APPROVED = "Approved"


@strawberry.enum
class AssigneeType(Enum):
    USER = "User"
    PROJECT_MEMBER = "GraphQLProjectMember"
    PROJECT_GROUP = "GraphQLProjectGroup"


@strawberry.input(name="taskItem")
class GraphQLTaskItem:
    id: str
    type: TaskItemType


@strawberry.input
class GraphQLAssignee:
    id: str
    type: AssigneeType


@strawberry.federation.type(keys=["id"])
class GraphQLTask:
    id: strawberry.ID
    name: str
    description: str
    due_date: datetime.date
    author_id: str = strawberry.federation.field(shareable=True)
    status: TaskStatus
    comments: list[Annotated["GraphQLComment", strawberry.lazy("schema.comment")]] | None
    commits: list[Annotated["GraphQLCommit", strawberry.lazy("schema.commit")]]
    reporting_schema: Annotated["GraphQLReportingSchema", strawberry.lazy("schema.reporting_schema")]
    reporting_schema_id: str = strawberry.federation.field(shareable=True)
    assignee_id: str | None = strawberry.federation.field(shareable=True)
    assigned_group_id: str | None = strawberry.federation.field(shareable=True)

    @strawberry.field
    async def item(self, info: Info) -> Union[GraphQLSchemaElement, GraphQLSchemaCategory]:
        session = info.context.get("session")
        if self.category_id:
            schema_category = await session.get(models_category.SchemaCategory, self.category_id)
            return GraphQLSchemaCategory(
                **schema_category.dict(),
                elements=[],
                commits=[],
                reporting_schema=None,
            )
        else:
            schema_element = await session.get(models_category.SchemaElement, self.element_id)
            return GraphQLSchemaElement(
                **schema_element.dict(exclude={"schema_category_id", "source_id"}),
                schema_category=None,
                source=None,
                commits=[],
            )


async def query_tasks(
    info: Info,
    reporting_schema_id: str,
    commit_id: Optional[str] = None,
    filters: Optional[TaskFilters] = None,
) -> list[GraphQLTask]:
    """Get all tasks connected to a reporting schema"""

    session = get_session(info)
    # auth_query = select(models_schema.ReportingSchema).where(models_schema.ReportingSchema.id == reporting_schema_id)
    # reporting_schema = (await session.exec(auth_query)).first()
    # _ = await authenticate(info, reporting_schema.project_id)

    if commit_id:
        query = select(models_task.Task).where(models_task.TaskCommitLink.commit_id == commit_id)
    elif not reporting_schema_id:
        query = select(models_task.Task)
    else:
        query = select(models_task.Task).where(models_task.Task.reporting_schema_id == reporting_schema_id)

    query = await graphql_options(info, query)

    if filters:
        query = filter_model_query(models_task.Task, filters, query)
    tasks = await session.exec(query)
    return tasks.all()


async def add_task_mutation(
    info: Info,
    reporting_schema_id: str,
    name: str,
    due_date: datetime.date,
    item: GraphQLTaskItem,
    description: str,
    status: TaskStatus,
    assignee: Optional[GraphQLAssignee] = None,
) -> GraphQLTask:
    """Add a Task to a Reporting Schema"""

    session = get_session(info)
    user = get_user(info)

    # fetches the reporting schema
    reporting_schema = await session.get(models_schema.ReportingSchema, reporting_schema_id)
    members = await authenticate(info, reporting_schema.project_id)

    schema_part = await session.get(
        models_category.SchemaCategory if item.type == TaskItemType.Category else models_element.SchemaElement,
        item.id,
    )

    if not schema_part:
        raise DatabaseItemNotFound(f"{item.task_type} with id: {item.task_id} was not found")

    if assignee.type == AssigneeType.PROJECT_MEMBER:
        for member in members:
            if assignee.id == member.id:
                assignee.id = member.user_id

    if assignee.type == AssigneeType.PROJECT_GROUP:
        await authenticate_group(info, group_id=assignee.id, project_id=reporting_schema.project_id)

    # creates a task database class
    task = models_task.Task(
        name=name,
        due_date=due_date,
        description=description,
        element_id=item.id if item.type == TaskItemType.Element else None,
        element=schema_part if item.type == TaskItemType.Element else None,
        category_id=item.id if item.type == TaskItemType.Category else None,
        category=schema_part if item.type == TaskItemType.Category else None,
        reporting_schema_id=reporting_schema_id,
        reporting_schema=reporting_schema,
        author_id=user.claims.get("oid"),
        status=status.value,
        assignee_id=assignee.id if assignee.type == AssigneeType.PROJECT_MEMBER else None,
        assigned_group_id=assignee.id if assignee.type == AssigneeType.PROJECT_GROUP else None,
    )

    # fetches the repository that belongs to the reporting schema
    repository = (
        await session.exec(
            select(models_repository.Repository)
            .where(models_repository.Repository.reporting_schema_id == reporting_schema.id)
            .options(selectinload(models_repository.Repository.commits))
            .options(selectinload(models_repository.Repository.reporting_schema))
        )
    ).first()

    head_commit = (
        await session.exec(
            select(models_commit.Commit)
            .where(models_commit.Commit.id == repository.head.id)
            .options(selectinload(models_commit.Commit.schema_categories))
            .options(selectinload(models_commit.Commit.schema_elements))
            .options(selectinload(models_commit.Commit.tasks))
        )
    ).first()

    commit = models_commit.Commit.copy_from_parent(head_commit, author_id=user.claims.get("oid"))
    commit.short_id = commit.id[:8]
    commit.tasks.append(task)

    session.add(commit)
    session.add(task)

    await session.commit()
    await session.refresh(commit)
    await session.refresh(task)
    query = select(models_task.Task).where(models_task.Task.reporting_schema == reporting_schema)
    query = await graphql_options(info, query)
    await session.exec(query)

    return task


async def update_task_mutation(
    info: Info,
    id: str,
    name: Optional[str] = None,
    due_date: Optional[datetime.date] = None,
    item: Optional[GraphQLTaskItem] = None,
    description: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    assignee: Optional[GraphQLAssignee] = None,
    assigned_group_id: Optional[str] = None,
) -> GraphQLTask:
    """Update a Task"""

    session = info.context.get("session")
    user = info.context.get("user")

    task = await session.get(models_task.Task, id)
    if not task:
        raise DatabaseItemNotFound(f"Could not find Task with id: {id}")

    reporting_schema = await session.get(models_schema.ReportingSchema, task.reporting_schema_id)

    members = await authenticate(info, reporting_schema.project_id)

    repository = (
        await session.exec(
            select(models_repository.Repository)
            .where(models_repository.Repository.reporting_schema_id == reporting_schema.id)
            .options(selectinload(models_repository.Repository.commits))
            .options(selectinload(models_repository.Repository.reporting_schema))
        )
    ).first()

    head_commit = (
        await session.exec(
            select(models_commit.Commit)
            .where(models_commit.Commit.id == repository.head.id)
            .options(selectinload(models_commit.Commit.schema_categories))
            .options(selectinload(models_commit.Commit.schema_elements))
            .options(selectinload(models_commit.Commit.tasks))
        )
    ).first()

    commit = models_commit.Commit.copy_from_parent(head_commit, author_id=user.claims.get("oid"))
    commit.short_id = commit.id[:8]
    commit.tasks.remove(task)

    if item:
        schema_part = await session.get(
            models_category.SchemaCategory if item.type == TaskItemType.Category else models_element.SchemaElement,
            item.id,
        )
    else:
        schema_part = None

    if assignee.type == AssigneeType.PROJECT_MEMBER:
        for member in members:
            if assignee.id == member.id:
                assignee.id = member.user_id

    if assigned_group_id:
        await authenticate_group(info, group_id=assigned_group_id, project_id=reporting_schema.project_id)

    kwargs = {
        "name": name,
        "due_date": due_date,
        "description": description,
        "element_id": item.id if item and item.type == TaskItemType.Element else None,
        "element": schema_part if item and item.type == TaskItemType.Element else None,
        "category_id": item.id if item and item.type == TaskItemType.Category else None,
        "category": schema_part if item and item.type == TaskItemType.Category else None,
        "status": status.value if status else None,
        "assignee_id": assignee.id if assignee and assignee.type == AssigneeType.PROJECT_MEMBER else None,
        "assigned_group_id": assignee.id if assignee and assignee.type == AssigneeType.PROJECT_GROUP else None,
    }

    for key, value in kwargs.items():
        if value:
            setattr(task, key, value)

    commit.tasks.append(task)
    session.add(commit)
    session.add(task)

    await session.commit()
    await session.refresh(commit)
    await session.refresh(task)

    query = select(models_task.Task).where(models_task.Task.id == task.id)
    query = await graphql_options(info, query)

    await session.exec(query)
    return task


async def delete_task_mutation(info: Info, id: str) -> str:
    """Delete a Task"""

    session = info.context.get("session")
    user = info.context.get("user")

    task = (
        await session.exec(
            select(models_task.Task)
            .where(models_task.Task.id == id)
            .options(selectinload(models_task.Task.commits))
            .options(selectinload(models_task.Task.reporting_schema))
            .options(selectinload(models_task.Task.comments))
            .options(selectinload(models_task.Task.element))
            .options(selectinload(models_task.Task.category))
        )
    ).first()
    if not task:
        raise DatabaseItemNotFound(f"Could not find Task with id: {id}")

    reporting_schema = await session.get(models_schema.ReportingSchema, task.reporting_schema_id)

    _ = await authenticate(info, reporting_schema.project_id)

    repository = (
        await session.exec(
            select(models_repository.Repository)
            .where(models_repository.Repository.reporting_schema_id == reporting_schema.id)
            .options(selectinload(models_repository.Repository.commits))
            .options(selectinload(models_repository.Repository.reporting_schema))
        )
    ).first()

    head_commit = (
        await session.exec(
            select(models_commit.Commit)
            .where(models_commit.Commit.id == repository.head.id)
            .options(selectinload(models_commit.Commit.schema_categories))
            .options(selectinload(models_commit.Commit.schema_elements))
            .options(selectinload(models_commit.Commit.tasks))
        )
    ).first()

    commit = models_commit.Commit.copy_from_parent(head_commit, author_id=user.claims.get("oid"))
    commit.short_id = commit.id[:8]
    commit.tasks.remove(task)
    session.add(commit)

    await session.commit()
    await session.refresh(commit)

    await session.delete(task)
    await session.commit()
    return id


async def graphql_options(info, query):
    """
    Optionally "select IN" loads the needed collections of a
    Schema Element based on the request provided in the info

    Args:
        info (Info): request information
        query: current query provided

    Returns: updated query
    """

    if task_field := [field for field in info.selected_fields if field.name == "tasks"]:
        if [field for field in task_field[0].selections if field.name == "comments"]:
            query = query.options(selectinload(models_task.Task.comments))
        if [field for field in task_field[0].selections if field.name == "commits"]:
            query = query.options(selectinload(models_task.Task.commits))
        if [field for field in task_field[0].selections if field.name == "reportingSchema"]:
            query = query.options(selectinload(models_task.Task.reporting_schema))
        if [field for field in task_field[0].selections if field.name == "category"]:
            query = query.options(selectinload(models_task.Task.category))
        if [field for field in task_field[0].selections if field.name == "element"]:
            query = query.options(selectinload(models_task.Task.element))
    return query
