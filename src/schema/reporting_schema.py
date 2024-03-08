from typing import TYPE_CHECKING, Annotated, Optional

import strawberry
from lcacollect_config.context import get_session
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlalchemy.orm import selectinload
from sqlmodel import select
from strawberry import UNSET
from strawberry.types import Info

import models.commit as models_commit
import models.reporting_schema as models_schema
import models.repository as models_repository
import models.schema_category as models_category
import models.schema_template as models_template
from core.validate import authenticate, authenticate_project
from schema.inputs import ReportingSchemaFilters

if TYPE_CHECKING:  # pragma: no cover
    from schema.schema_category import GraphQLSchemaCategory


@strawberry.type
class GraphQLReportingSchema:
    id: str
    name: str
    categories: list[Annotated["GraphQLSchemaCategory", strawberry.lazy("schema.schema_category")]] | None
    project_id: str
    template_id: str | None


@strawberry.input
class ReportingSchemaInput:
    id: str
    name: Optional[str] = UNSET
    project_id: Optional[str] = UNSET
    template_id: Optional[str] = UNSET


@strawberry.type
class GraphQLReportingCreationSchema:
    id: str
    name: str
    project_id: str | None


async def query_reporting_schemas(
    info: Info, project_id: str, filters: Optional[ReportingSchemaFilters] = None
) -> list[GraphQLReportingSchema]:
    """Query a reporting schema using project_id"""

    session = get_session(info)
    await authenticate_project(info, project_id)
    await authenticate(info, project_id, check_public=True)

    query = select(models_schema.ReportingSchema)

    if project_id:
        query = query.where(models_schema.ReportingSchema.project_id == project_id)

    query = await graphql_options(info, query)

    if filters:
        query = filter_model_query(models_schema.ReportingSchema, filters, query)

    reporting_schema = (await session.exec(query)).all()

    return reporting_schema


async def add_reporting_schema_mutation(
    info: Info,
    template_id: str,
    project_id: str,
    name: Optional[str] = None,
) -> GraphQLReportingCreationSchema:
    """
    Add a Reporting Schema to a project.
    Concurrently updates the Schema Template to
    hold the Reporting Schema.
    """

    session = info.context.get("session")
    user = info.context.get("user")

    reporting_schema = models_schema.ReportingSchema(name=name, project_id=project_id)

    await authenticate(info, project_id)
    await authenticate_project(info, project_id)

    template = await session.get(models_template.SchemaTemplate, template_id)
    reporting_schema.template_id = template.id
    session.add(reporting_schema)
    await session.commit()

    template.original_id = reporting_schema.id

    repository = models_repository.Repository(
        reporting_schema=reporting_schema, reporting_schema_id=reporting_schema.id
    )
    commit = models_commit.Commit(author_id=user.claims.get("oid"))
    repository.commits.append(commit)

    session.add(commit)
    await session.commit()

    session.add(template)
    session.add(repository)

    await session.commit()
    await session.refresh(reporting_schema)
    await session.refresh(repository)

    return reporting_schema


async def add_reporting_schema_from_template_mutation(
    info: Info, template_id: str, project_id: str, name: Optional[str]
) -> GraphQLReportingCreationSchema:
    """Copy a Reporting Schema from a template to a project"""

    session = info.context.get("session")
    user = info.context.get("user")

    await authenticate(info, project_id)
    await authenticate_project(info, project_id)

    query = (
        select(models_schema.ReportingSchema)
        .join(models_template.SchemaTemplate)
        .where(
            models_template.SchemaTemplate.id == template_id,
            models_schema.ReportingSchema.id == models_template.SchemaTemplate.original_id,
        )
        .options(selectinload(models_schema.ReportingSchema.categories))
    )
    # fetch empty(original_id) reporting schema as template
    template_schema = (await session.exec(query)).one()

    # create new reporting schema with project_id
    reporting_schema = models_schema.ReportingSchema(name=name or template_schema.name, project_id=project_id)
    reporting_schema.template_id = template_schema.template_id

    # add to history table
    repository = models_repository.Repository(
        reporting_schema=reporting_schema, reporting_schema_id=reporting_schema.id
    )
    commit = models_commit.Commit(author_id=user.claims.get("oid"))
    repository.commits.append(commit)

    categories = []
    for old_category in template_schema.categories:
        new_category = models_category.SchemaCategory(
            **old_category.dict(exclude={"id", "project_id", "reporting_schema_id"}),
            project_id=project_id,
        )
        categories.append(new_category)

    reporting_schema.categories = categories
    commit.schema_categories = categories

    session.add(commit)
    session.add(reporting_schema)
    session.add(repository)

    await session.commit()
    await session.refresh(reporting_schema)
    await session.refresh(repository)

    return reporting_schema


async def update_reporting_schema_mutation(
    info: Info, id: str, name: Optional[str] = None, project_id: Optional[str] = None
) -> GraphQLReportingSchema:
    """Update a Reporting Schema"""

    session = get_session(info)
    reporting_schema = await session.get(models_schema.ReportingSchema, id)
    if not reporting_schema:
        raise DatabaseItemNotFound(f"Could not find Reporting Schema with id: {id}")

    await authenticate(info, reporting_schema.project_id)
    await authenticate_project(info, project_id)

    kwargs = {"name": name}
    for key, value in kwargs.items():
        if value:
            setattr(reporting_schema, key, value)

    session.add(reporting_schema)

    await session.commit()
    await session.refresh(reporting_schema)

    query = select(models_schema.ReportingSchema).where(models_schema.ReportingSchema.id == reporting_schema.id)
    query = await graphql_options(info, query)
    await session.exec(query)
    return reporting_schema


async def delete_reporting_schema_mutation(info: Info, id: str) -> str:
    """Delete a Reporting Schema"""

    session = get_session(info)
    reporting_schema = await session.get(models_schema.ReportingSchema, id)
    await authenticate(info, reporting_schema.project_id)
    await session.delete(reporting_schema)
    await session.commit()
    return id


async def graphql_options(info, query):
    """
    Optionally "select IN" loads the needed collections of a
    Reporting Schema based on the request provided in the info

    Args:
        info (Info): request information
        query: current query provided

    Returns: updated query
    """

    if schema_field := [field for field in info.selected_fields if field.name == "reportingSchemas"]:
        if category_field := [field for field in schema_field[0].selections if field.name == "categories"]:
            if [field for field in category_field[0].selections if field.name in ("elements", "typeCodeElement")]:
                query = query.options(
                    selectinload(models_schema.ReportingSchema.categories).options(
                        selectinload(models_category.SchemaCategory.elements),
                        selectinload(models_category.SchemaCategory.type_code_element),
                    )
                )
            else:
                query = query.options(selectinload(models_schema.ReportingSchema.categories))
    return query
