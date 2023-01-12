from typing import Callable

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.commit import Commit
from models.schema_category import SchemaCategory


@pytest.mark.asyncio
async def test_get_schema_categories(
    client: AsyncClient,
    schema_categories,
    reporting_schemas,
    member_mocker,
    get_response: Callable,
):
    query = """
        query ($reportingSchemaId: String!, $commitId: String = null){
            schemaCategories(reportingSchemaId: $reportingSchemaId, commitId: $commitId){
                id
                path
                name
                description
                reportingSchemaId
                elements {
                    name
                }
                commits {
                    shortId
                }
            }
        }
    """
    variables = {"reportingSchemaId": f"{reporting_schemas[0].id}"}

    data = await get_response(client, query, variables=variables)
    assert isinstance(data["schemaCategories"], list)
    assert set(data["schemaCategories"][0].keys()) == {
        "id",
        "path",
        "name",
        "description",
        "commits",
        "elements",
        "reportingSchemaId",
    }


@pytest.mark.asyncio
async def test_get_schema_categories_with_filters(
    client: AsyncClient,
    schema_categories,
    reporting_schemas,
    member_mocker,
    get_response: Callable,
):
    query = """
        query ($reportingSchemaId: String!, $commitId: String = null)  {
            schemaCategories(reportingSchemaId: $reportingSchemaId, commitId: $commitId, filters: {name: {contains: 
            "0"}}) {
                id
                path
                name
                description
            }
        }
    """
    variables = {"reportingSchemaId": f"{reporting_schemas[0].id}"}

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
        mutation($reportingSchemaId: String!) {
            addSchemaCategory(name: "Schema Category 0", reportingSchemaId: $reportingSchemaId) {
                name
                reportingSchemaId
            }
        }
    """
    variables = {"reportingSchemaId": f"{reporting_schemas[0].id}"}

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()

    data = await get_response(client, mutation, variables=variables)
    assert data["addSchemaCategory"] == {
        "name": "Schema Category 0",
        "reportingSchemaId": reporting_schemas[0].id,
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
        mutation($id: String!, $path: String = null, $description: String = null, $name: String = null) {
            updateSchemaCategory(id: $id, path: $path, description: $description, name: $name) {
                id
                path
                name
                description
            }
        }
    """

    async with AsyncSession(db) as session:
        query = select(Commit)
        commits_before = await session.exec(query)
        commits_before = commits_before.all()

    variables = {
        "id": schema_categories[0].id,
        "name": schema_categories[0].name,
        "path": schema_categories[0].id + "/",
        "description": "updated!",
    }

    data = await get_response(client, mutation, variables=variables)
    assert data["updateSchemaCategory"] == {
        "name": schema_categories[0].name,
        "id": schema_categories[0].id,
        "path": schema_categories[0].id + "/",
        "description": "updated!",
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
