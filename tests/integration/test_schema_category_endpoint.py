from typing import Callable

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.commit import Commit
from models.schema_category import SchemaCategory
from models.typecode import TypeCodeElement


@pytest.mark.asyncio
async def test_get_schema_categories(
    client: AsyncClient,
    schema_categories,
    reporting_schemas,
    project_exists_mock,
    member_mocker,
    get_response: Callable,
):
    query = """
        query ($reportingSchemaId: String!, $commitId: String = null){
            schemaCategories(reportingSchemaId: $reportingSchemaId, commitId: $commitId){
                id
                description
                reportingSchemaId
                typeCodeElement {
                    name
                }
                elements {
                    name
                }
                commits {
                    shortId
                }
            }
        }
    """
    variables = {"reportingSchemaId": reporting_schemas[0].id}

    data = await get_response(client, query, variables=variables)
    assert isinstance(data["schemaCategories"], list)
    assert set(data["schemaCategories"][0].keys()) == {
        "id",
        "description",
        "commits",
        "elements",
        "reportingSchemaId",
        "typeCodeElement",
    }


@pytest.mark.asyncio
async def test_get_schema_categories_with_filters(
    client: AsyncClient,
    schema_categories,
    reporting_schemas,
    project_exists_mock,
    member_mocker,
    get_response: Callable,
):
    query = """
        query ($reportingSchemaId: String!, $commitId: String = null)  {
            schemaCategories(reportingSchemaId: $reportingSchemaId, commitId: $commitId, filters: {description: {contains: 
            "description 0"}}) {
                id
                description
            }
        }
    """
    variables = {"reportingSchemaId": reporting_schemas[0].id}

    data = await get_response(client, query, variables=variables)
    assert len(data["schemaCategories"]) == 1


@pytest.mark.asyncio
async def test_create_schema_category(
    client: AsyncClient,
    reporting_schemas,
    commits,
    repositories,
    schema_elements,
    tasks,
    comments,
    db,
    member_mocker,
    get_response: Callable,
):
    mutation = """
        mutation($reportingSchemaId: String!, $typeCodeElementId: String!) {
            addSchemaCategory(reportingSchemaId: $reportingSchemaId, typeCodeElementId: $typeCodeElementId) {
                typeCodeElementId
                reportingSchemaId
            }
        }
    """
    async with AsyncSession(db) as session:
        type_code_element = (await session.exec(select(TypeCodeElement))).first()

    variables = {"reportingSchemaId": reporting_schemas[0].id, "typeCodeElementId": type_code_element.id}

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()

    data = await get_response(client, mutation, variables=variables)
    assert data["addSchemaCategory"] == {
        "reportingSchemaId": reporting_schemas[0].id,
        "typeCodeElementId": type_code_element.id,
    }

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()

    assert len(commits_after) != len(commits_before)


@pytest.mark.asyncio
async def test_update_schema_category(
    client: AsyncClient,
    schema_categories,
    commits,
    repositories,
    reporting_schemas,
    schema_elements,
    db,
    member_mocker,
    get_response: Callable,
):
    mutation = """
        mutation($id: String!, $typeCodeElementId: String,  $description: String = null) {
            updateSchemaCategory(id: $id, description: $description, typeCodeElementId: $typeCodeElementId) {
                id
                description
                typeCodeElement{
                    name
                }
            }
        }
    """

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()
        type_code_element = (await session.exec(select(TypeCodeElement))).first()

    variables = {"id": schema_categories[0].id, "description": "updated!", "typeCodeElementId": type_code_element.id}

    data = await get_response(client, mutation, variables=variables)
    assert data["updateSchemaCategory"] == {
        "id": schema_categories[0].id,
        "description": "updated!",
        "typeCodeElement": {"name": "Name 1"},
    }
    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()

    assert len(commits_after) != len(commits_before)


@pytest.mark.asyncio
async def test_delete_schema_category(
    client: AsyncClient,
    db,
    schema_categories,
    commits,
    repositories,
    reporting_schemas,
    schema_elements,
    member_mocker,
    get_response: Callable,
):
    mutation = """
        mutation($id: String!) {
            deleteSchemaCategory(id: $id) 
        }

    """
    variables = {"id": schema_categories[0].id}

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()

    await get_response(client, mutation, variables=variables)

    async with AsyncSession(db) as session:
        query = select(SchemaCategory)
        _categories = await session.exec(query)
        _categories = _categories.all()

    assert len(_categories) == len(schema_categories) - 1

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_after = await session.exec(query)
        commits_after = commits_after.all()

    assert len(commits_after) != len(commits_before)
    print(commits_after)
