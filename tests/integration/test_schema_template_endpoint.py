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
                original {
                    name
                    categories {
                        typeCodeElement {
                            name
                        }
                    }
                }
            }
        }
    """

    data = await get_response(client, query)

    assert len(data["schemaTemplates"]) == 3
    assert data["schemaTemplates"][0] == {
        "name": "Template 0",
        "original": {"name": "Reporting Schema 0", "categories": [{"typeCodeElement": {"name": "Part"}}]},
    }


@pytest.mark.asyncio
async def test_get_schema_templates_with_filters(
    client: AsyncClient, is_admin_mock, schema_templates, get_response: Callable
):
    query = """
        query {
            schemaTemplates(filters: {domain: {equal: "test 0"}}) {
                name
                original {
                    name
                }
            }
        }
    """

    data = await get_response(client, query)

    assert len(data["schemaTemplates"]) == 1
    assert data["schemaTemplates"][0] == {
        "name": "Template 0",
        "original": {
            "name": "Reporting Schema 0",
        },
    }


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient, get_response: Callable, is_admin_mock, type_code_elements):
    mutation = """
        mutation($name: String!, $domain: String, $typeCodes: [GraphQLTypeCodeElementInput!]){
            addSchemaTemplate(name: $name, domain: $domain, typeCodes: $typeCodes) {
                name
            }
        }
    """
    variables = {
        "name": "Schema Template 0",
        "domain": "lca",
        "typeCodes": [
            {"id": type_code_elements[0].id, "parentPath": type_code_elements[0].parent_path},
            {"id": type_code_elements[1].id, "parentPath": type_code_elements[1].parent_path},
            {"id": type_code_elements[3].id, "parentPath": type_code_elements[3].parent_path},
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
                original {
                    name
                    categories {
                        typeCodeElement {
                            name
                            code
                        }
                    }
                }
            }
        }
    """

    data = await get_response(client, query)

    assert len(data["schemaTemplates"]) == 1
    assert data["schemaTemplates"][0] == {
        "name": "Schema Template 0",
        "original": {
            "name": "Schema Template 0",
            "categories": [
                {"typeCodeElement": {"name": "Name 1", "code": "1"}},
                {"typeCodeElement": {"name": "Name 2", "code": "11"}},
            ],
        },
    }


@pytest.mark.asyncio
async def test_update_schema_template(client: AsyncClient, get_response: Callable, is_admin_mock, type_code_elements):
    mutation = """
        mutation($name: String!, $domain: String, $typeCodes: [GraphQLTypeCodeElementInput!]){
            addSchemaTemplate(name: $name, domain: $domain, typeCodes: $typeCodes) {
                id
                name
            }
        }
    """
    variables = {
        "name": "Schema Template 0",
        "domain": "lca",
        "typeCodes": [
            {"id": type_code_elements[0].id, "parentPath": type_code_elements[0].parent_path},
        ],
    }
    data = await get_response(client, mutation, variables=variables)

    query = """
         mutation($id: String!, $name: String!, $domain: String, $typeCodes: [GraphQLTypeCodeElementInput!]) {
            updateSchemaTemplate(id: $id, name: $name, domain: $domain, typeCodes: $typeCodes) {
                name
                original {
                    name
                    categories {
                        typeCodeElement {
                            name
                            code
                        }
                    }
                }
            }
        }
    """
    variables = {
        "id": data["addSchemaTemplate"]["id"],
        "name": "test",
        "typeCodes": [
            {"id": type_code_elements[0].id, "parentPath": type_code_elements[0].parent_path},
            {"id": type_code_elements[1].id, "parentPath": type_code_elements[1].parent_path},
            {"id": type_code_elements[3].id, "parentPath": type_code_elements[3].parent_path},
        ],
    }

    data = await get_response(client, query, variables=variables)

    assert data == {
        "updateSchemaTemplate": {
            "name": "test",
            "original": {
                "name": "test",
                "categories": [
                    {"typeCodeElement": {"name": "Name 1", "code": "1"}},
                    {"typeCodeElement": {"name": "Name 2", "code": "11"}},
                ],
            },
        }
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
