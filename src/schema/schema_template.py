from typing import Optional

import strawberry
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlmodel import select
from strawberry import UNSET
from strawberry.types import Info

import models.reporting_schema as models_reporting
import models.schema_category as models_category
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


@strawberry.input
class GraphQLTypeCodeElementInput:
    id: str
    name: str
    code: str
    level: int


async def query_schema_templates(
    info: Info, filters: Optional[SchemaTemplateFilters] = None
) -> list[GraphQLSchemaTemplate]:
    """Query Schema Templates"""
    templates = []
    session = info.context.get("session")
    query = (
        select(models_template.SchemaTemplate, models_reporting.ReportingSchema)
        .join(models_reporting.ReportingSchema)
        .where(models_reporting.ReportingSchema.project_id == None)
    )
    if filters:
        query = filter_model_query(models_template.SchemaTemplate, filters, query=query)
    schema_templates = (await session.exec(query)).all()

    for template, schema in schema_templates:
        query = select(models_category.SchemaCategory).where(
            models_category.SchemaCategory.reporting_schema_id == schema.id
        )
        schema_categories = (await session.exec(query)).all()

        joined_schema = schema_reporting.GraphQLReportingSchema(
            id=schema.id,
            name=schema.name,
            categories=schema_categories,
            project_id=schema.project_id,
            template_id=template.id,
        )
        template = GraphQLSchemaTemplate(id=template.id, name=template.name, schema=joined_schema)
        templates.append(template)

    return templates


async def add_schema_template_mutation(
    info: Info, name: str, type_codes: Optional[list[GraphQLTypeCodeElementInput]] = None
) -> GraphQLSchemaTemplate:
    """Add a Schema Template"""
    session = info.context.get("session")
    schema_template = models_template.SchemaTemplate(name=name)
    session.add(schema_template)

    reporting_schema = models_reporting.ReportingSchema(name=name, template=schema_template)
    session.add(reporting_schema)

    if type_codes:
        for type_code in type_codes:
            schema_category = models_category.SchemaCategory(
                name=type_code.name, path=type_code.code, depth=type_code.level, reporting_schema=reporting_schema
            )
            session.add(schema_category)

    await session.commit()
    await session.refresh(schema_category)

    schema_template.original_id = reporting_schema.id
    session.add(schema_template)
    await session.commit()

    await session.refresh(schema_template)

    query = select(models_category.SchemaCategory).where(
        models_category.SchemaCategory.reporting_schema_id == reporting_schema.id
    )
    schema_categories = (await session.exec(query)).all()

    joined_schema = schema_reporting.GraphQLReportingSchema(
        id=reporting_schema.id,
        name=reporting_schema.name,
        categories=schema_categories,
        project_id=reporting_schema.project_id,
        template_id=schema_template.id,
    )
    template = GraphQLSchemaTemplate(id=schema_template.id, name=schema_template.name, schema=joined_schema)

    return template


async def update_schema_template_mutation(
    info: Info, id: str, name: Optional[str] = None, type_codes: Optional[list[GraphQLTypeCodeElementInput]] = None
) -> GraphQLSchemaTemplate:
    """Update a Schema Template"""

    session = info.context.get("session")
    query = (
        select(models_template.SchemaTemplate, models_reporting.ReportingSchema)
        .join(models_reporting.ReportingSchema)
        .where(models_template.SchemaTemplate.id == id)
    )
    for schema_template, reporting_schema in (await session.exec(query)).all():
        if not schema_template:
            raise DatabaseItemNotFound(f"Could not find Schema Template with id: {id}")

        if name:
            schema_template.name = name
            reporting_schema.name = name

        session.add(schema_template)
        session.add(reporting_schema)

        if type_codes:
            query = select(models_category.SchemaCategory).where(
                models_category.SchemaCategory.reporting_schema_id == reporting_schema.id
            )
            schema_categories = (await session.exec(query)).all()
            # remove
            for schema_category in schema_categories:
                schema_category.reporting_schema_id = None
                session.delete(schema_category)
                await session.commit()

            # update
            for type_code in type_codes:
                new_schema_category = models_category.SchemaCategory(
                    name=type_code.name, path=type_code.code, depth=type_code.level, reporting_schema=reporting_schema
                )
                session.add(new_schema_category)

    await session.commit()
    await session.refresh(schema_template)
    await session.refresh(reporting_schema)

    query = select(models_category.SchemaCategory).where(
        models_category.SchemaCategory.reporting_schema_id == reporting_schema.id
    )
    schema_categories = (await session.exec(query)).all()

    joined_schema = schema_reporting.GraphQLReportingSchema(
        id=reporting_schema.id,
        name=reporting_schema.name,
        categories=schema_categories,
        project_id=reporting_schema.project_id,
        template_id=reporting_schema.id,
    )

    return GraphQLSchemaTemplate(id=schema_template.id, name=schema_template.name, schema=joined_schema)


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
