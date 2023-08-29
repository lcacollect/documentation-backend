from typing import Callable

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models.commit import Commit
from models.schema_element import SchemaElement
from models.source import ProjectSource
from schema.schema_element import Unit


@pytest.mark.asyncio
async def test_get_schema_elements(
    client: AsyncClient, schema_elements, project_exists_mock, member_mocker, get_response: Callable
):
    query = """
        query getElements($schemaCategoryIds: [String!]!, $commitId: String = null){
            schemaElements(schemaCategoryIds: $schemaCategoryIds, commitId: $commitId) {
                id
                name
                quantity
                unit
                description
                commits {
                    shortId
                }
            }
        }
    """
    variables = {"schemaCategoryIds": [schema_elements[0].schema_category_id]}

    data = await get_response(client, query, variables=variables)

    assert isinstance(data["schemaElements"], list)
    assert set(data["schemaElements"][0].keys()) == {
        "id",
        "name",
        "quantity",
        "unit",
        "description",
        "commits",
    }


@pytest.mark.asyncio
async def test_get_schema_elements_with_filters(
    client: AsyncClient, schema_elements, project_exists_mock, member_mocker, get_response: Callable
):
    query = """
        query getElements($schemaCategoryIds: [String!]!, $commitId: String = null){
            schemaElements(schemaCategoryIds: $schemaCategoryIds, commitId: $commitId, filters: {name: {contains: "0"}}) {
                id
                name
                quantity
                unit
                description
            }
        }
    """
    variables = {"schemaCategoryIds": [schema_elements[0].schema_category_id]}

    data = await get_response(client, query, variables=variables)
    assert len(data["schemaElements"]) == 1


@pytest.mark.asyncio
async def test_create_schema_element_from_source(
    client: AsyncClient,
    db,
    commits,
    schema_categories,
    project_sources,
    member_mocker,
    blob_client_mock,
    get_response: Callable,
):
    mutation = """
        mutation addElement($schemaCategoryIds: [String!]!, $sourceId: String!, $objectIds: [String!]!, $units: [Unit!], $quantities: [Float!]){
            addSchemaElementFromSource(schemaCategoryIds: $schemaCategoryIds, sourceId: $sourceId, objectIds: $objectIds, units: $units, quantities: $quantities){
                name
                unit
                description
                schemaCategory {
                    id
                    name
                }
                quantity
                source {
                    id
                    name
                }
            }
        }
    """

    async with AsyncSession(db) as session:
        source = (await session.exec(select(ProjectSource).where(ProjectSource.type == "csv"))).first()

    variables = {
        "schemaCategoryIds": [schema_categories[0].id, schema_categories[0].id],
        "sourceId": source.id,
        "objectIds": ["0", "2"],
        "units": [Unit.M2.name, Unit.M3.name],
        "quantities": [123.456, 456.789],
    }

    data = await get_response(client, mutation, variables=variables)
    assert set(data["addSchemaElementFromSource"][0].keys()) == {
        "name",
        "unit",
        "description",
        "schemaCategory",
        "quantity",
        "source",
    }


@pytest.mark.asyncio
async def test_create_schema_element_from_source_xlsx(
    client: AsyncClient,
    db,
    commits,
    schema_categories,
    xlsx_source,
    member_mocker,
    blob_client_mock_xlsx,
    get_response: Callable,
):
    mutation = """
        mutation addElement($schemaCategoryIds: [String!]!, $sourceId: String!, $objectIds: [String!]!, $units: [Unit!], $quantities: [Float!]){
            addSchemaElementFromSource(schemaCategoryIds: $schemaCategoryIds, sourceId: $sourceId, objectIds: $objectIds, units: $units, quantities: $quantities){
                name
                unit
                description
                schemaCategory {
                    id
                    name
                }
                quantity
                source {
                    id
                    name
                }
            }
        }
    """

    async with AsyncSession(db) as session:
        source = (await session.exec(select(ProjectSource).where(ProjectSource.type == "xlsx"))).first()

    variables = {
        "schemaCategoryIds": [schema_categories[0].id, schema_categories[0].id],
        "sourceId": source.id,
        "objectIds": ["0", "2"],
        "units": [Unit.M2.name, Unit.M3.name],
        "quantities": [123.456, 456.789],
    }

    data = await get_response(client, mutation, variables=variables)
    assert set(data["addSchemaElementFromSource"][0].keys()) == {
        "name",
        "unit",
        "description",
        "schemaCategory",
        "quantity",
        "source",
    }


@pytest.mark.asyncio
async def test_create_schema_element(
    client: AsyncClient,
    db,
    schema_categories,
    schema_elements,
    repositories,
    commits,
    member_mocker,
    get_response: Callable,
):
    mutation = """
        mutation addElement($schemaCategoryId: String!) {
            addSchemaElement(name: "Schema Element 0", schemaCategoryId: $schemaCategoryId, unit: M2, quantity: 1, description: "", assemblyId: "assembly-Id" ) {
                name
                schemaCategory {
                    id
                }
                quantity
                unit
                description
                assemblyId
            }
        }
    """
    variables = {"schemaCategoryId": schema_categories[0].id}

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()

    data = await get_response(client, mutation, variables=variables)
    assert data["addSchemaElement"] == {
        "name": "Schema Element 0",
        "schemaCategory": {"id": schema_categories[0].id},
        "quantity": 1.0,
        "unit": Unit.M2.name,
        "description": "",
        "assemblyId": "assembly-Id",
    }
    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()

    assert len(commits_after) != len(commits_before)


@pytest.mark.asyncio
async def test_update_schema_element(
    client: AsyncClient,
    db,
    schema_elements,
    commits,
    repositories,
    schema_categories,
    member_mocker,
    get_response: Callable,
):
    mutation = """
        mutation updateElements($elements: [SchemaElementUpdateInput!]!){
            updateSchemaElements(schemaElements: $elements) {
                id
                quantity
                unit
                name
                description
                assemblyId
            }
        }
    """
    variables = {
        "elements": {
            "id": schema_elements[1].id,
            "description": "Description 1",
            "quantity": 1.0,
            "unit": Unit.M3.name,
            "assemblyId": "assembly-Id",
        }
    }

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()

    data = await get_response(client, mutation, variables=variables)
    assert data["updateSchemaElements"] == [
        {
            "name": "Schema Element 1",
            "id": schema_elements[1].id,
            "description": "Description 1",
            "quantity": 1.0,
            "unit": Unit.M3.name,
            "assemblyId": "assembly-Id",
        }
    ]

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()

    assert len(commits_after) != len(commits_before)


async def test_delete_schema_element(
    db,
    client: AsyncClient,
    schema_elements,
    repositories,
    schema_categories,
    commits,
    member_mocker,
    get_response: Callable,
):
    mutation = """
        mutation($id: String!) {
            deleteSchemaElement(id: $id) 
        }
    """
    variables = {"id": schema_elements[0].id}

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()

    assert await get_response(client, mutation, variables=variables)

    async with AsyncSession(db) as session:
        query = select(SchemaElement)
        _elements = await session.exec(query)
        _elements = _elements.all()

    assert len(_elements) == len(schema_elements) - 1

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()

    assert len(commits_after) != len(commits_before)
