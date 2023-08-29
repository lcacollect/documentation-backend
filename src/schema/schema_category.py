from typing import TYPE_CHECKING, Annotated, Optional

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
from core.validate import authenticate
from schema.inputs import SchemaCategoryFilters

if TYPE_CHECKING:  # pragma: no cover
    from schema.commit import GraphQLCommit
    from schema.reporting_schema import GraphQLReportingSchema
    from schema.schema_element import GraphQLSchemaElement


@strawberry.type
class GraphQLSchemaCategory:
    id: strawberry.ID
    name: str
    description: str | None
    reporting_schema_id: str | None
    path: str

    @strawberry.field
    def depth(self) -> int:
        if not self.path or self.path == "/":
            return 0
        else:
            return self.path.count("/")

    reporting_schema: Annotated["GraphQLReportingSchema", strawberry.lazy("schema.reporting_schema")]
    elements: list[Annotated["GraphQLSchemaElement", strawberry.lazy("schema.schema_element")]] | None
    commits: list[Annotated["GraphQLCommit", strawberry.lazy("schema.commit")]] | None


async def query_schema_categories(
    info: Info,
    reporting_schema_id: str,
    commit_id: Optional[str] = None,
    filters: Optional[SchemaCategoryFilters] = None,
) -> list[GraphQLSchemaCategory]:
    """Get all Schema Categories of a Reporting Schema"""

    session = get_session(info)

    auth_query = select(models_schema.ReportingSchema).where(models_schema.ReportingSchema.id == reporting_schema_id)
    reporting_schema = (await session.exec(auth_query)).first()
    await authenticate(info, reporting_schema.project_id, check_public=True)

    if commit_id:
        query = select(models_category.SchemaCategory).where(models_category.CategoryCommitLink.commit_id == commit_id)
    else:
        query = select(models_schema.SchemaCategory).where(
            models_category.SchemaCategory.reporting_schema_id == reporting_schema_id
        )

    query = await graphql_options(info, query)

    if filters:
        query = filter_model_query(models_category.SchemaCategory, filters, query)
    categories = await session.exec(query)
    return categories.all()


async def add_schema_category_mutation(
    info: Info,
    reporting_schema_id: str,
    name: Optional[str] = None,
    path: Optional[str] = None,
    description: Optional[str] = None,
) -> GraphQLSchemaCategory:
    """Add a Schema Category to a Reporting Schema"""

    session = info.context.get("session")
    user = info.context.get("user")

    # fetches the reporting schema
    reporting_schema = (
        await session.exec(
            select(models_schema.ReportingSchema).where(models_schema.ReportingSchema.id == reporting_schema_id)
        )
    ).first()

    await authenticate(info, reporting_schema.project_id)

    # creates a schema category database class
    schema_category = models_category.SchemaCategory(
        path=path,
        name=name,
        description=description,
        reporting_schema=reporting_schema,
        reporting_schema_id=reporting_schema_id,
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

    # project_member_data = get_project_member(reporting_schema.project_id)
    head_commit = (
        await session.exec(
            select(models_commit.Commit)
            .where(models_commit.Commit.id == repository.head.id)
            .options(selectinload(models_commit.Commit.schema_categories))
            .options(selectinload(models_commit.Commit.schema_elements))
            .options(selectinload(models_commit.Commit.tasks))
        )
    ).first()

    # copies the latest commit in the repository
    commit = models_commit.Commit.copy_from_parent(head_commit, author_id=user.claims.get("oid"))
    commit.short_id = commit.id[:8]
    # adds the schema category to the commit
    commit.schema_categories.append(schema_category)

    session.add(commit)
    session.add(schema_category)

    await session.commit()
    await session.refresh(commit)
    await session.refresh(schema_category)

    query = select(models_category.SchemaCategory).where(
        models_category.SchemaCategory.reporting_schema == reporting_schema
    )
    query = await graphql_options(info, query)

    await session.exec(query)

    return schema_category


async def update_schema_category_mutation(
    info: Info,
    id: str,
    name: Optional[str] = None,
    path: Optional[str] = None,
    description: Optional[str] = None,
) -> GraphQLSchemaCategory:
    """Update a Schema Category"""

    session = get_session(info)
    user = get_user(info)

    schema_category = await session.get(models_category.SchemaCategory, id)
    if not schema_category:
        raise DatabaseItemNotFound(f"Could not find Schema Category with id: {id}")

    # fetches the reporting schema
    reporting_schema = await session.get(models_schema.ReportingSchema, schema_category.reporting_schema_id)

    await authenticate(info, reporting_schema.project_id)

    repository = (
        await session.exec(
            select(models_repository.Repository)
            .where(models_repository.Repository.reporting_schema_id == reporting_schema.id)
            .options(selectinload(models_repository.Repository.commits))
            .options(selectinload(models_repository.Repository.reporting_schema))
        )
    ).first()

    # fetch the latest commit
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
    commit.schema_categories.remove(schema_category)

    kwargs = {"name": name, "path": path, "description": description}
    for key, value in kwargs.items():
        if value:
            setattr(schema_category, key, value)

    commit.schema_categories.append(schema_category)
    session.add(commit)
    session.add(schema_category)

    await session.commit()
    await session.refresh(commit)
    await session.refresh(schema_category)

    query = select(models_category.SchemaCategory).where(models_category.SchemaCategory.id == id)
    query = await graphql_options(info, query)
    await session.exec(query)

    return schema_category


async def delete_schema_category_mutation(info: Info, id: str) -> str:
    """Delete a Schema Category"""

    session = info.context.get("session")
    user = info.context.get("user")

    schema_category = (
        await session.exec(
            select(models_category.SchemaCategory)
            .where(models_category.SchemaCategory.id == id)
            .options(selectinload(models_category.SchemaCategory.commits))
            .options(selectinload(models_category.SchemaCategory.reporting_schema))
            .options(selectinload(models_category.SchemaCategory.elements))
        )
    ).first()

    if not schema_category:
        raise DatabaseItemNotFound(f"Could not find Schema Category with id: {id}")

    reporting_schema = await session.get(models_schema.ReportingSchema, schema_category.reporting_schema_id)

    await authenticate(info, reporting_schema.project_id)

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

    elements = (
        await session.exec(
            select(models_element.SchemaElement)
            .where(models_element.SchemaElement.schema_category_id == id)
            .options(selectinload(models_element.SchemaElement.schema_category))
            .options(selectinload(models_element.SchemaElement.commits))
        )
    ).all()

    commit = models_commit.Commit.copy_from_parent(head_commit, author_id=user.claims.get("oid"))
    commit.short_id = commit.id[:8]
    commit.schema_categories.remove(schema_category)

    for element in elements:
        commit.schema_elements.remove(element)
        await session.delete(element)

    session.add(commit)

    await session.commit()
    await session.refresh(commit)

    await session.delete(schema_category)
    await session.commit()

    return id


async def graphql_options(info, query):
    """
    Optionally "select IN" loads the needed collections of a Schema Category
    based on the request provided in the info

    Args:
        info (Info): request information
        query: current query provided

    Returns: updated query
    """

    if category_field := [field for field in info.selected_fields if field.name == "schemaCategories"]:
        if [field for field in category_field[0].selections if field.name == "commits"]:
            query = query.options(selectinload(models_category.SchemaCategory.commits))
        if [field for field in category_field[0].selections if field.name == "elements"]:
            query = query.options(selectinload(models_category.SchemaCategory.elements))
        if [field for field in category_field[0].selections if field.name == "reportingSchema"]:
            query = query.options(selectinload(models_category.SchemaCategory.reporting_schema))
    return query


def is_project_member(info: Info, members) -> bool:
    user = info.context.get("user")
    for member in members:
        if member.user_id == user.claims.get("oid") or user.claims.get("scp") == "lca_super_admin":
            return True

    return False
