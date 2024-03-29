from typing import Optional

import strawberry
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlalchemy.orm import Query, selectinload
from sqlmodel import select
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
    schemas: list[schema_reporting.GraphQLReportingSchema] | None


@strawberry.input
class GraphQLTypeCodeElementInput:
    id: str | None
    name: str
    code: str
    level: int | None
    parent_path: str  # "/parents_parent_id/parent_id" or "/" for no parent


async def query_schema_templates(
    info: Info, filters: Optional[SchemaTemplateFilters] = None
) -> list[GraphQLSchemaTemplate]:
    """Query Schema Templates"""
    session = info.context.get("session")

    query = select(models_template.SchemaTemplate)
    query = check_return_values(info, query)

    if filters:
        query = filter_model_query(models_template.SchemaTemplate, filters, query=query)

    schema_templates = (await session.exec(query)).unique().all()

    return schema_templates


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
        type_code_ids = [type_code.id for type_code in type_codes]
        type_code_path_map = {}
        for type_code in type_codes:
            schema_category = ""
            if getattr(type_code, "parent_path", "/") == "/":
                schema_category = models_category.SchemaCategory(
                    name=type_code.name, path="/", reporting_schema=reporting_schema
                )
                type_code_path_map["/"] = schema_category
            else:
                parent_codes = list(filter(None, type_code.parent_path.split("/")))
                if all(parent_code in type_code_ids for parent_code in parent_codes):
                    schema_category = models_category.SchemaCategory(
                        name=type_code.name,
                        path=construct_parent_path(type_code.parent_path, type_code_path_map),
                        reporting_schema=reporting_schema,
                    )
                    type_code_path_map[type_code.parent_path] = schema_category
            if schema_category:
                session.add(schema_category)

    await session.commit()

    schema_template.original_id = reporting_schema.id
    session.add(schema_template)
    await session.commit()

    query = select(models_template.SchemaTemplate).where(models_template.SchemaTemplate.id == schema_template.id)
    query = check_return_values(info, query)

    schema_template = (await session.exec(query)).first()

    return schema_template


def construct_parent_path(path: str, type_code_path_map: dict[str, models_category.SchemaCategory]) -> str:
    parent_path = "/" if len(path.split("/")) == 2 else "/".join(path.split("/")[:-1])
    parent_category = type_code_path_map.get(parent_path)
    if parent_category.path == "/":
        return parent_category.path + parent_category.id
    return parent_category.path + "/" + parent_category.id


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

        query = select(models_category.SchemaCategory).where(
            models_category.SchemaCategory.reporting_schema_id == reporting_schema.id
        )
        schema_categories = (await session.exec(query)).all()

        # remove
        for schema_category in schema_categories:
            schema_category.reporting_schema_id = None
            session.delete(schema_category)
            await session.commit()

        if type_codes:
            # add
            type_code_ids = [type_code.id for type_code in type_codes]
            for type_code in type_codes:
                schema_category = ""
                if getattr(type_code, "parent_path", "/") == "/":
                    schema_category = models_category.SchemaCategory(
                        name=type_code.name, path="/", reporting_schema=reporting_schema
                    )
                else:
                    parent_codes = list(filter(None, type_code.parent_path.split("/")))
                    if all(parent_code in type_code_ids for parent_code in parent_codes):
                        schema_category = models_category.SchemaCategory(
                            name=type_code.name,
                            path=type_code.parent_path,
                            reporting_schema=reporting_schema,
                        )
                if schema_category:
                    session.add(schema_category)

        await session.commit()

    query = select(models_template.SchemaTemplate).where(models_template.SchemaTemplate.id == schema_template.id)
    query = check_return_values(info, query)

    schema_template = (await session.exec(query)).first()

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


def check_return_values(info: Info, query: Query) -> Query:
    joined_query = query
    for field in info.selected_fields:
        for template_fields in field.selections:
            if template_fields.name == "schemas":
                joined_query = query.options(selectinload(models_template.SchemaTemplate.schemas)).where(
                    models_reporting.ReportingSchema.project_id == None
                )
                for schema_field in template_fields.selections:
                    if schema_field.name == "categories":
                        joined_query = query.options(
                            selectinload(models_template.SchemaTemplate.schemas).selectinload(
                                models_reporting.ReportingSchema.categories
                            )
                        ).where(models_reporting.ReportingSchema.project_id == None)
    return joined_query
