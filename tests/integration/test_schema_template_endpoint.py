from typing import Callable

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from models.schema_template import SchemaTemplate


@pytest.mark.asyncio
async def test_get_schema_templates(client: AsyncClient, schema_templates, get_response: Callable):
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
async def test_get_schema_templates_with_filters(client: AsyncClient, schema_templates, get_response: Callable):
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
async def test_create_template(client: AsyncClient, get_response: Callable):
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
            {"name": "name", "id": "Idcode", "level": 1, "parentPath": "/"},
            {"name": "name2", "id": "Idcode2", "level": 1, "parentPath": "/Idcode"},
            {"name": "name4", "id": "Idcode4", "level": 1, "parentPath": "/Idcode2/Idcode3"},
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
    assert data["schemaTemplates"] == [
        {
            "name": "Schema Template 0",
            "schemas": [
                {
                    "name": "Schema Template 0",
                    "categories": [
                        {"name": "name", "path": "/", "depth": 0},
                        {"name": "name2", "path": "/Idcode", "depth": 1},
                    ],
                }
            ],
        }
    ]


@pytest.mark.asyncio
async def test_update_schema_template(client: AsyncClient, get_response: Callable):
    mutation = """
        mutation($name: String!, $typeCodes: [GraphQLTypeCodeElementInput!]){
            addSchemaTemplate(name: $name, typeCodes: $typeCodes) {
                id
                name
            }
        }
    """
    variables = {"name": "Schema Template 0", "typeCodes": {"name": "name", "id": "111", "level": 1, "parentPath": "/"}}
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
            {"id": "112", "name": "name2", "level": 3, "parentPath": "/"},
            {"id": "113", "name": "name3", "level": 2, "parentPath": "/112"},
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
                    {"name": "name3", "path": "/112", "depth": 1},
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_delete_schema_templates(client: AsyncClient, schema_templates, db, get_response: Callable):
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
