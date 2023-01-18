from typing import Optional

import strawberry
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlmodel import select
from strawberry import UNSET
from strawberry.types import Info

import models.reporting_schema as models_reporting
import models.schema_template as models_template
import schema.reporting_schema as schema_reporting
from schema.inputs import SchemaTemplateFilters


@strawberry.type
class GraphQLSchemaTemplate:
    id: str
    name: str
    schema: schema_reporting.GraphQLReportingSchema | None


@strawberry.input
class ReportingSchemaInput:
    id: str
    name: Optional[str] = UNSET
    tmplt: Optional[str] = UNSET


async def query_schema_templates(
    info: Info, filters: Optional[SchemaTemplateFilters] = None
) -> list[GraphQLSchemaTemplate]:

    """Query Schema Templates"""

    session = info.context.get("session")
    query = (
        select(models_template.SchemaTemplate, models_reporting.ReportingSchema)
        .join(models_reporting.ReportingSchema)
        .where(models_reporting.ReportingSchema.project_id == None)
    )
    if filters:
        query = filter_model_query(models_template.SchemaTemplate, filters, query=query)
    schema_templates = (await session.exec(query)).all()

    return [
        GraphQLSchemaTemplate(id=template.id, name=template.name, schema=schema)
        for template, schema in schema_templates
    ]


async def add_schema_template_mutation(info: Info, name: str) -> GraphQLSchemaTemplate:

    """Add a Schema Template"""

    session = info.context.get("session")
    schema_template = models_template.SchemaTemplate(name=name)
    session.add(schema_template)

    await session.commit()
    await session.refresh(schema_template)

    query = select(models_template.SchemaTemplate).where(models_template.SchemaTemplate.id == schema_template.id)

    await session.exec(query)
    return schema_template


async def update_schema_template_mutation(info: Info, id: str, name: Optional[str] = None) -> GraphQLSchemaTemplate:

    """Update a Schema Template"""

    session = info.context.get("session")
    schema_template = await session.get(models_template.SchemaTemplate, id)

    if not schema_template:
        raise DatabaseItemNotFound(f"Could not find Schema Template with id: {id}")

    kwargs = {"id": id, "name": name}
    for key, value in kwargs.items():
        if value:
            setattr(schema_template, key, value)

    session.add(schema_template)

    await session.commit()
    await session.refresh(schema_template)

    query = select(models_template.SchemaTemplate).where(models_template.SchemaTemplate.id == schema_template.id)

    await session.exec(query)
    return schema_template


async def delete_schema_template_mutation(info: Info, id: str) -> str:

    """Delete a Schema Template"""

    session = info.context.get("session")
    schema_template = await session.get(models_template.SchemaTemplate, id)
    await session.delete(schema_template)
    await session.commit()
    return id


def is_project_member(info: Info, members) -> bool:

    """
    Check whether the user trying to mutate/query
    is a member of that project and/or an admin user.
    Returns true if is a project member or an admin
    """

    user = info.context.get("user")
    for member in members:
        if member.user_id == user.claims.get("oid") or user.claims.get("scp") == "lca_super_admin":
            return True

    return False
