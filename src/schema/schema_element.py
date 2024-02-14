import logging
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Optional, Union

import strawberry
from fastapi import HTTPException
from lcacollect_config.context import get_session, get_user
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession
from strawberry.scalars import JSON
from strawberry.types import Info

import models.commit as models_commit
import models.reporting_schema as models_schema
import models.repository as models_repository
import models.schema_category as models_category
import models.schema_element as models_element
import models.source as models_source
import schema.source as schema_source
from core.validate import authenticate
from exceptions import SourceElementCreationError
from schema.inputs import SchemaElementFilters

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    from schema.commit import GraphQLCommit
    from schema.schema_category import GraphQLSchemaCategory
    from schema.source import GraphQLProjectSource

SPECKLE_OBJECTS_TO_INCLUDE = ["@Doors", "@Floors", "@Walls", "@Roofs", "@Windows"]
MATERIALS_MAPPING = {
    "@Doors": "Concrete",
    "@banister": "Glass",
    "@facade": "Glass",
    "@columns": "Steel",
}


@strawberry.enum
class Unit(Enum):
    M = "m"
    M2 = "m2"
    M3 = "m3"
    L = "l"
    KG = "kg"
    PCS = "pcs"
    TONNES = "tonnes"
    TONNES_KM = "t*km"
    NONE = None


@strawberry.federation.type(keys=["id"])
class GraphQLSchemaElement:
    id: strawberry.ID = strawberry.federation.field(shareable=True)
    name: str = strawberry.federation.field(shareable=True)
    quantity: float = strawberry.federation.field(shareable=True)
    unit: Unit = strawberry.federation.field(shareable=True)
    description: str | None = strawberry.federation.field(shareable=True)
    schema_category: Annotated["GraphQLSchemaCategory", strawberry.lazy("schema.schema_category")]
    commits: list[Annotated["GraphQLCommit", strawberry.lazy("schema.commit")]]
    source: Annotated["GraphQLProjectSource", strawberry.lazy("schema.source")] | None
    assembly_id: str | None = strawberry.federation.field(shareable=True)
    result: JSON | None = strawberry.federation.field(shareable=True)


async def query_schema_elements(
    info: Info,
    schema_category_ids: list[str],
    element_id: Optional[str] = None,
    commit_id: Optional[str] = None,
    filters: Optional[SchemaElementFilters] = None,
) -> list[GraphQLSchemaElement]:
    """Get all schema elements for a list of categories"""
    session = get_session(info)

    schema_category = (
        await session.exec(
            select(models_category.SchemaCategory)
            .where(models_schema.SchemaCategory.id == schema_category_ids[0])
            .options(selectinload(models_category.SchemaCategory.reporting_schema))
        )
    ).first()

    if schema_category:
        await authenticate(info, schema_category.reporting_schema.project_id, check_public=True)

    if commit_id:
        query = select(models_element.SchemaElement).where(models_element.ElementCommitLink.commit_id == commit_id)
    elif element_id:
        query = select(models_element.SchemaElement).where(models_element.SchemaElement.id == element_id)
    else:
        query = select(models_element.SchemaElement).where(
            col(models_element.SchemaElement.schema_category_id).in_(schema_category_ids)
        )

    query = await graphql_options(info, query)

    if filters:
        query = filter_model_query(models_category.SchemaElement, filters, query)

    elements = await session.exec(query)
    return elements.all()


async def add_schema_element_mutation(
    info: Info,
    schema_category_id: str,
    name: str,
    quantity: float,
    unit: Unit,
    description: str,
    assembly_id: Optional[str] = None,
) -> GraphQLSchemaElement:
    """Add a Schema Element to a Schema Category"""

    commit, schema_category, session = await fetch_models(info, schema_category_id)
    await authenticate(info, schema_category.reporting_schema.project_id)

    schema_element = models_element.SchemaElement(
        name=name,
        quantity=quantity,
        unit=unit.value,
        description=description,
        schema_category=schema_category,
        schema_category_id=schema_category_id,
        assembly_id=assembly_id,
    )

    # adds the schema element to the commit
    commit.schema_elements.append(schema_element)
    session.add(commit)
    session.add(schema_element)
    await session.commit()
    await session.refresh(commit)
    await session.refresh(schema_element)

    query = select(models_element.SchemaElement).where(
        models_element.SchemaElement.schema_category_id == schema_category_id
    )
    query = await graphql_options(info, query, "addSchemaElement")

    await session.exec(query)

    return schema_element


@strawberry.input()
class SchemaElementUpdateInput:
    id: str
    name: Optional[str] = None
    schema_category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Unit | None = None
    description: Optional[str] = None
    result: Optional[JSON] = None
    assembly_id: Optional[str] = None


async def update_schema_elements_mutation(
    info: Info,
    schema_elements: list[SchemaElementUpdateInput],
) -> list[GraphQLSchemaElement]:
    """Update Schema Elements"""

    session = info.context.get("session")

    schema_element = await session.get(models_element.SchemaElement, schema_elements[0].id)
    commit, schema_category, _ = await fetch_models(info, schema_element.schema_category_id)
    await authenticate(info, schema_category.reporting_schema.project_id)

    schema_element_models = [
        await update_schema_element_model(session, commit, schema_element_input)
        for schema_element_input in schema_elements
    ]

    session.add(commit)

    await session.commit()
    await session.refresh(commit)
    [await session.refresh(schema_element) for schema_element in schema_element_models]

    query = select(models_element.SchemaElement).where(
        col(models_element.SchemaElement.id).in_([schema_element.id for schema_element in schema_element_models])
    )
    query = await graphql_options(info, query)

    _schema_elements = (await session.exec(query)).all()
    return _schema_elements


async def update_schema_element_model(
    session: AsyncSession, commit: models_commit.Commit, schema_element_input: SchemaElementUpdateInput
) -> models_element.SchemaElement:
    schema_element = await session.get(models_element.SchemaElement, schema_element_input.id)

    if not schema_element:
        raise DatabaseItemNotFound(f"Could not find Schema Element with id: {schema_element_input.id}")

    try:
        commit.schema_elements.remove(schema_element)
    except ValueError:
        logger.exception("No schema element in commit object")

    kwargs = {
        "name": schema_element_input.name,
        "schema_category_id": schema_element_input.schema_category,
        "quantity": schema_element_input.quantity,
        "unit": schema_element_input.unit.value if schema_element_input.unit is not None else None,
        "description": schema_element_input.description,
        "result": schema_element_input.result,
        "assembly_id": schema_element_input.assembly_id,
    }

    for key, value in kwargs.items():
        if value:
            setattr(schema_element, key, value)

    commit.schema_elements.append(schema_element)
    session.add(schema_element)

    return schema_element


async def delete_schema_element_mutation(info: Info, id: str) -> str:
    """Delete a Schema Element"""

    session = info.context.get("session")
    schema_element = (
        await session.exec(
            select(models_element.SchemaElement)
            .where(models_element.SchemaElement.id == id)
            .options(selectinload(models_element.SchemaElement.commits))
            .options(selectinload(models_element.SchemaElement.schema_category))
            .options(selectinload(models_element.SchemaElement.source))
        )
    ).first()

    if not schema_element:
        raise DatabaseItemNotFound(f"Could not find Schema Element with id: {id}")

    commit, schema_category, _ = await fetch_models(info, schema_element.schema_category_id)
    await authenticate(info, schema_category.reporting_schema.project_id)

    try:
        commit.schema_elements.remove(schema_element)
    except ValueError:
        logger.exception("No schema element in commit object")
    else:
        session.add(commit)

        await session.commit()
        await session.refresh(commit)

    await session.delete(schema_element)
    await session.commit()

    return id


async def graphql_options(info, query, base_field: str = "schemaElements"):
    """
    Optionally "select IN" loads the needed collections of a
    Schema Element based on the request provided in the info

    Args:
        info (Info): request information
        query: current query provided
        base_field: base field to look up in

    Returns: updated query
    """

    if element_field := [field for field in info.selected_fields if field.name == base_field]:
        if [field for field in element_field[0].selections if field.name == "commits"]:
            query = query.options(selectinload(models_element.SchemaElement.commits))
        if [field for field in element_field[0].selections if field.name == "schemaCategory"]:
            query = query.options(selectinload(models_element.SchemaElement.schema_category))
        if [field for field in element_field[0].selections if field.name == "source"]:
            query = query.options(selectinload(models_element.SchemaElement.source))
    return query


async def add_schema_element_from_source_mutation(
    info: Info,
    schema_category_ids: list[str],
    source_id: str,
    object_ids: list[str],
    units: Optional[list[Unit]] = None,
    quantities: Optional[list[float]] = None,
):
    """Add a Schema Element to a Schema Category from with data from a Project Source"""

    commit, schema_category, session = await fetch_models(info, schema_category_ids[0])
    await authenticate(info, schema_category.reporting_schema.project_id)
    elements = []
    source = await session.get(models_source.ProjectSource, source_id)
    if source.type == schema_source.ProjectSourceType.SPECKLE.name:
        raise NotImplementedError()
        # elements = await speckle_to_elements(elements, object_ids, schema_category, schema_category_ids, source)
    elif source.type in (schema_source.ProjectSourceType.CSV.value, schema_source.ProjectSourceType.XLSX.value):
        elements = await file_data_to_elements(schema_category_ids, source, object_ids, quantities, units)
    else:
        raise SourceElementCreationError(
            f"Can not add elements from source: {source.id} with source type: {source.type}"
        )

    for schema_element in elements:
        commit.schema_elements.append(schema_element)
        session.add(schema_element)

    session.add(commit)
    await session.commit()
    await session.refresh(commit)
    [await session.refresh(element) for element in elements]

    query = select(models_element.SchemaElement).where(
        col(models_element.SchemaElement.id).in_([element.id for element in elements])
    )
    query = await graphql_options(info, query, "addSchemaElementFromSource")

    elements = (await session.exec(query)).all()
    return elements


async def fetch_models(
    info: Info, schema_category_id: str
) -> tuple[models_commit.Commit, models_category.SchemaCategory, AsyncSession]:
    """Fetches the latest commit and schema category"""
    session = get_session(info)
    user = get_user(info)

    schema_category = await get_category(session, schema_category_id)
    repository = await get_repository(session, schema_category.reporting_schema.id)
    head_commit = await get_head_commit(session, repository.head.id)

    commit = models_commit.Commit.copy_from_parent(head_commit, author_id=user.claims.get("oid"))
    commit.short_id = commit.id[:8]

    return commit, schema_category, session


async def get_category(session: AsyncSession, schema_category_id: str) -> models_category.SchemaCategory:
    query = (
        select(models_category.SchemaCategory)
        .where(models_category.SchemaCategory.id == schema_category_id)
        .options(selectinload(models_category.SchemaCategory.reporting_schema))
    )
    category = await session.exec(query)
    return category.one()


async def get_repository(session: AsyncSession, repository_id: str) -> models_repository.Repository:
    query = (
        select(models_repository.Repository)
        .where(models_repository.Repository.reporting_schema_id == repository_id)
        .options(selectinload(models_repository.Repository.commits))
        .options(selectinload(models_repository.Repository.reporting_schema))
    )
    repository = await session.exec(query)
    return repository.one()


async def get_head_commit(session: AsyncSession, head_id: str) -> models_commit.Commit:
    query = (
        select(models_commit.Commit)
        .where(models_commit.Commit.id == head_id)
        .options(selectinload(models_commit.Commit.schema_categories))
        .options(selectinload(models_commit.Commit.schema_elements))
        .options(selectinload(models_commit.Commit.tasks))
    )
    commit = await session.exec(query)

    return commit.one()


async def speckle_to_elements(elements, object_ids, schema_category, schema_category_id, source):
    """
    Converts Speckle Objects to Schema Elements
    and adds them to a Schema Category
    """

    client = SpeckleClient(source.meta_fields["speckle_url"])
    client.authenticate_with_token("aa96984792480ab6881967274ced7b4d31d9db91fc")
    stream = client.stream.get(id=source.data_id)
    transport = ServerTransport(client=client, stream_id=stream.id)
    for object_id in object_ids:
        object = operations.receive(object_id, transport)
        if not object:
            raise HTTPException(404, f"Can not find an element with object id: {object_id}")
        object_dict = object.__dict__
        interpretation = source.interpretation
        elements.append(
            models_element.SchemaElement(
                name=object_dict.get(interpretation.get("name", ""), ""),
                unit=object_dict.get(interpretation.get("unit", ""), ""),
                description=object_dict.get(interpretation.get("description", ""), ""),
                source=source,
                source_id=source.id,
                schema_category=schema_category,
                schema_category_id=schema_category_id,
                quantity=object_dict.get(interpretation.get("quantity", ""), ""),
            )
        )
    return elements


async def file_data_to_elements(
    schema_category_ids: list[str],
    source: models_source.ProjectSource,
    objects_ids: list[str],
    quantities: list[float],
    units: list[Unit],
):
    elements = []
    interpretation = source.interpretation
    headers, file_data = source.data

    if (
        len(objects_ids) != len(quantities)
        or len(objects_ids) != len(units)
        or len(objects_ids) != len(schema_category_ids)
    ):
        raise SourceElementCreationError(
            f"Number of object_ids: {len(objects_ids)} must match number of quantities: {len(quantities)}, units: {len(units)} and schema_categories: {len(schema_category_ids)}"
        )

    for idx, object_id in enumerate(objects_ids):
        try:
            row = file_data[int(object_id)]
        except IndexError:
            raise SourceElementCreationError(f"Object with id: {object_id} does not exist on source: {source.id}")
        except ValueError:
            raise SourceElementCreationError(f"Id: {object_id} is not an integer!")
        try:
            elements.append(
                models_element.SchemaElement(
                    name=row[interpretation.get("interpretationName", "interpretationName")],
                    description=row[interpretation.get("description", "description")]
                    if "description" in interpretation
                    else None,
                    quantity=quantities[idx] if quantities[idx] else 0,
                    unit=units[idx].value,
                    source_id=source.id,
                    schema_category_id=schema_category_ids[idx],
                    meta_fields={"source_object_index": interpretation.get("id", None)},
                )
            )
        except KeyError as error:
            raise SourceElementCreationError(f"Field: {error} does not exist in source data of source: {source.id}")
    return elements
