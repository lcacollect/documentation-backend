from typing import Callable

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.schema_template import SchemaTemplate


@pytest.mark.asyncio
async def test_get_schema_templates(client: AsyncClient, is_admin_mock, schema_templates, get_response: Callable):
    query = """
        query {
            schemaTemplates {
                name
                schemas {
                    name
                    categories {
                        name
                    }
                }
            }
        }
    """

    data = await get_response(client, query)
    assert len(data["schemaTemplates"]) == 3
    assert data["schemaTemplates"][0] == {
        "name": "Template 0",
        "schemas": [{"name": "Reporting Schema 0", "categories": [{"name": "Category 0"}]}],
    }


@pytest.mark.asyncio
async def test_get_schema_templates_with_filters(
    client: AsyncClient, is_admin_mock, schema_templates, get_response: Callable
):
    query = """
        query {
            schemaTemplates(filters: {name: {contains: "Template 0"}}) {
                name
                schemas {
                    name
                }
            }
        }
    """

    data = await get_response(client, query)
    assert len(data["schemaTemplates"]) == 1
    assert data["schemaTemplates"][0] == {
        "name": "Template 0",
        "schemas": [
            {
                "name": "Reporting Schema 0",
            }
        ],
    }


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient, get_response: Callable, is_admin_mock):
    mutation = """
        mutation($name: String!, $typeCodes: [GraphQLTypeCodeElementInput!]){
            addSchemaTemplate(name: $name, typeCodes: $typeCodes) {
                name
            }
        }
    """
    variables = {
        "name": "Schema Template 0",
        "typeCodes": [
            {"id": "test", "name": "name", "code": "Idcode", "level": 1, "parentPath": "/"},
            {"id": "test2", "name": "name2", "code": "Idcode2", "level": 1, "parentPath": "/test"},
            {"id": "test4", "name": "name4", "code": "Idcode4", "level": 1, "parentPath": "/test/test3"},
        ],
    }
    data = await get_response(client, mutation, variables=variables)
    assert data["addSchemaTemplate"] == {
        "name": "Schema Template 0",
    }

    query = """
        query {
            schemaTemplates {
                name
                schemas {
                    name
                    categories {
                        id
                        name
                        path
                        depth
                    }
                }
            }
        }
    """

    data = await get_response(client, query)
    assert len(data["schemaTemplates"]) == 1
    assert data["schemaTemplates"][0] == {
        "name": "Schema Template 0",
        "schemas": [
            {
                "name": "Schema Template 0",
                "categories": [
                    {
                        "id": data["schemaTemplates"][0].get("schemas")[0].get("categories")[0].get("id"),
                        "name": "name",
                        "path": "/",
                        "depth": 0,
                    },
                    {
                        "id": data["schemaTemplates"][0].get("schemas")[0].get("categories")[1].get("id"),
                        "name": "name2",
                        "path": f'/{data["schemaTemplates"][0].get("schemas")[0].get("categories")[0].get("id")}',
                        "depth": 1,
                    },
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_update_schema_template(client: AsyncClient, get_response: Callable, is_admin_mock):
    mutation = """
        mutation($name: String!, $typeCodes: [GraphQLTypeCodeElementInput!]){
            addSchemaTemplate(name: $name, typeCodes: $typeCodes) {
                id
                name
            }
        }
    """
    variables = {
        "name": "Schema Template 0",
        "typeCodes": {"id": "test", "name": "name", "code": "111", "level": 1, "parentPath": "/"},
    }
    data = await get_response(client, mutation, variables=variables)

    query = """
        mutation($id: String!, $name: String!, $typeCodes: [GraphQLTypeCodeElementInput!]) {
            updateSchemaTemplate(id: $id, name: $name, typeCodes: $typeCodes) {
                name
                schemas {
                    name
                    categories{
                        name
                        path
                        depth
                    }
                }
            }
        }
    """
    variables = {
        "id": data["addSchemaTemplate"]["id"],
        "name": "test",
        "typeCodes": [
            {"id": "test", "code": "112", "name": "name2", "level": 3, "parentPath": "/"},
            {"id": "test2", "code": "113", "name": "name3", "level": 2, "parentPath": "/test"},
        ],
    }

    data = await get_response(client, query, variables=variables)
    assert data["updateSchemaTemplate"] == {
        "name": "test",
        "schemas": [
            {
                "name": "test",
                "categories": [
                    {"name": "name2", "path": "/", "depth": 0},
                    {"name": "name3", "path": "/test", "depth": 1},
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_delete_schema_templates(
    client: AsyncClient, schema_templates, db, get_response: Callable, is_admin_mock
):
    query = f"""
        mutation {{
            deleteSchemaTemplate(id: "{schema_templates[0].id}")
        }}
    """
    assert await get_response(client, query)

    async with AsyncSession(db) as session:
        query = select(SchemaTemplate)
        _templates = await session.exec(query)
        _templates = _templates.all()

    assert len(_templates) == len(schema_templates) - 1
