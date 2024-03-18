from typing import Optional

import strawberry
from lcacollect_config.context import get_session
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
    original: schema_reporting.GraphQLReportingSchema | None
    domain: Optional[str] = None


@strawberry.input
class GraphQLTypeCodeElementInput:
    id: str
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
    info: Info,
    name: str,
    domain: Optional[str] = None,
    type_codes: Optional[list[GraphQLTypeCodeElementInput]] = None,
) -> GraphQLSchemaTemplate:
    """Add a Schema Template"""

    session = get_session(info)

    schema_template = models_template.SchemaTemplate(name=name, domain=domain)
    session.add(schema_template)

    # create empty ReportingSchema as template with typeCodes
    reporting_schema = models_reporting.ReportingSchema(name=name, template=schema_template)
    session.add(reporting_schema)

    # add child typecodes only with parents, others ignored
    await create_categories_by_typecodes(info, reporting_schema, type_codes)

    await session.commit()

    schema_template.original_id = reporting_schema.id
    session.add(schema_template)
    await session.commit()

    query = select(models_template.SchemaTemplate).where(models_template.SchemaTemplate.id == schema_template.id)
    query = check_return_values(info, query)

    schema_template = (await session.exec(query)).first()

    return schema_template


async def update_schema_template_mutation(
    info: Info,
    id: str,
    name: Optional[str] = None,
    domain: Optional[str] = None,
    type_codes: Optional[list[GraphQLTypeCodeElementInput]] = None,
) -> GraphQLSchemaTemplate:
    """Update a Schema Template"""

    session = info.context.get("session")

    # update only empty reporting schema, for new projects
    # older projects are not effected
    query = (
        select(models_template.SchemaTemplate, models_reporting.ReportingSchema)
        .join(
            models_reporting.ReportingSchema,
            models_reporting.ReportingSchema.id == models_template.SchemaTemplate.original_id,
        )
        .where(
            models_template.SchemaTemplate.id == id,
        )
    )

    for schema_template, reporting_schema in (await session.exec(query)).all():
        if not schema_template:
            raise DatabaseItemNotFound(f"Could not find Schema Template with id: {id}")

        # update template name and domain
        if name:
            schema_template.name = name
            reporting_schema.name = name
        if domain:
            schema_template.domain = domain
        session.add(schema_template)
        session.add(reporting_schema)

        # remove categories, because parent not having db connection to child
        query = select(models_category.SchemaCategory).where(
            models_category.SchemaCategory.reporting_schema_id == reporting_schema.id
        )
        schema_categories = (await session.exec(query)).all()

        for schema_category in schema_categories:
            schema_category.reporting_schema_id = None
            session.delete(schema_category)
            await session.commit()

        # add child typecodes only with parents, others ignored
        await create_categories_by_typecodes(info, reporting_schema, type_codes)

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


async def create_categories_by_typecodes(
    info: Info, reporting_schema: models_category.SchemaCategory, type_codes: list[GraphQLTypeCodeElementInput]
) -> GraphQLSchemaTemplate:
    "Add categories to reporting schema"
    session = info.context.get("session")
    if type_codes:
        type_code_ids = [type_code.id for type_code in type_codes]
        for type_code in type_codes:
            schema_category = ""
            # if "/" will be [], all([]) = true
            parent_codes = list(filter(None, type_code.parent_path.split("/")))
            if all(parent_code in type_code_ids for parent_code in parent_codes):
                try:
                    schema_category = models_category.SchemaCategory(
                        type_code_element_id=type_code.id, reporting_schema=reporting_schema
                    )
                except:
                    schema_category = ""
            if schema_category:
                session.add(schema_category)

        await session.commit()


def check_return_values(info: Info, query: Query) -> Query:
    joined_query = query
    for field in info.selected_fields:
        for template_fields in field.selections:
            if template_fields.name == "schemas" or "original":
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
                    for category in schema_field.selections:
                        if category.name == "typeCodeElement":
                            joined_query = query.options(
                                selectinload(models_template.SchemaTemplate.schemas)
                                .selectinload(models_reporting.ReportingSchema.categories)
                                .selectinload(models_category.SchemaCategory.type_code_element)
                            ).where(models_reporting.ReportingSchema.project_id == None)
    return joined_query
