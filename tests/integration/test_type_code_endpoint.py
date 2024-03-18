import base64
from typing import Callable

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_type_code_elements_not_admin(client: AsyncClient, type_code_elements, get_response: Callable):
    query = """
        query {
            typeCodeElements {
                name
                level
                parentPath
            }
        }
    """

    with pytest.raises(AssertionError) as excinfo:
        await get_response(client, query, variables=None)

    assert "User is not an admin" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_type_codes(client: AsyncClient, is_admin_mock, type_code_elements, get_response: Callable):
    query = """
        query {
            typeCodes {
                name
                elements {
                    name
                }
            }
        }
    """
    data = await get_response(client, query, variables=None)

    assert data
    assert data.get("typeCodes")
    assert data.get("typeCodes")[0].get("name") == "Type Code 0"
    assert data.get("typeCodes")[0].get("elements")


@pytest.mark.asyncio
async def test_get_type_code_elements(client: AsyncClient, type_code_elements, is_admin_mock, get_response: Callable):
    query = """
        query {
            typeCodeElements{
                code
                name
                level
                parentPath
            }
        }
    """

    data = await get_response(client, query)
    assert len(data["typeCodeElements"]) == 4
    assert data["typeCodeElements"][0] == {
        "code": "1",
        "name": "Name 1",
        "parentPath": "/",
        "level": 1,
    }


@pytest.mark.asyncio
async def test_add_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query {
            typeCodeElements {
                name
                level
            }
        }
    """

    data = await get_response(client, query, variables=None)
    assert len(data["typeCodeElements"]) == 0

    query = """
        mutation ($name: String!, $code: String!, $level: Int!, $parentPath: String){
            createTypeCodeElement(name: $name, code: $code, level: $level, parentPath: $parentPath) {
                id
            }
        }
    """
    variables = {"name": "test", "code": "test", "level": 1, "parentPath": "/"}
    data = await get_response(client, query, variables=variables)

    query = """
        query {
            typeCodeElements {
                code
                name
                parentPath
                level
            }
        }
    """

    data = await get_response(client, query, variables=None)
    assert len(data["typeCodeElements"]) == 1
    assert data["typeCodeElements"][0] == {"name": "test", "code": "test", "level": 1, "parentPath": "/"}


@pytest.mark.asyncio
async def test_update_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query {
            typeCodeElements {
                name
                level
            }
        }
    """

    data = await get_response(client, query, variables=None)
    assert len(data["typeCodeElements"]) == 0

    query = """
        mutation ($name: String!, $code: String!, $level: Int!){
            createTypeCodeElement(name: $name, code: $code, level: $level) {
                id
            }
        }
    """
    variables = {"name": "test", "code": "test", "level": 1}
    data = await get_response(client, query, variables=variables)
    query = """
        mutation ($id: String!, $name: String!, $code: String!){
            updateTypeCodeElement(id: $id, name: $name, code: $code) {
                name
                level
            }
        }
    """
    variables = {"id": data["createTypeCodeElement"]["id"], "name": "test2", "code": "code2"}
    data = await get_response(client, query, variables=variables)

    query = """
        query {
            typeCodeElements {
                name
                code
                level
            }
        }
    """

    data = await get_response(client, query, variables=None)
    assert len(data["typeCodeElements"]) == 1
    assert data["typeCodeElements"][0] == {
        "name": "test2",
        "code": "code2",
        "level": 1,
    }


@pytest.mark.asyncio
async def test_delete_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query {
            typeCodeElements {
                name
                level
            }
        }
    """

    data = await get_response(client, query, variables=None)
    assert len(data["typeCodeElements"]) == 0

    query = """
        mutation ($name: String!, $code: String!, $level: Int!){
            createTypeCodeElement(name: $name, code: $code, level: $level) {
                id
            }
        }
    """
    variables = {"name": "test", "code": "test", "level": 1}
    data = await get_response(client, query, variables=variables)

    query = """
        mutation ($id: String!){
            deleteTypeCodeElement(id: $id)
        }
    """
    variables = {"id": data["createTypeCodeElement"]["id"]}
    await get_response(client, query, variables=variables)

    query = """
        query {
            typeCodeElements {
                name
                level
            }
        }
    """

    data = await get_response(client, query, variables=None)
    assert len(data["typeCodeElements"]) == 0


@pytest.mark.asyncio
async def test_add_type_code_elements_from_source(
    client: AsyncClient, is_admin_mock, datafix_dir, get_response: Callable
):
    query = """
        query {
            typeCodeElements {
                name
                level
            }
        }
    """

    data = await get_response(client, query, variables=None)
    assert len(data["typeCodeElements"]) == 0

    query = """
        mutation($file: String!, $name: String!){
            createTypeCodeElementFromSource(file: $file, name: $name)
        }
    """
    with open(datafix_dir / "type_code_elements.csv", "rb") as file:
        encoded_file = base64.b64encode((file.read())).decode("utf-8")

    variables = {"name": "Type Code 1", "file": encoded_file}
    await get_response(client, query, variables=variables)

    query = """
        query {
            typeCodeElements {
                id
                code
                name
                level
                parentPath
            }
        }
    """

    data = await get_response(client, query, variables=None)

    assert len(data["typeCodeElements"]) == 3
    assert data["typeCodeElements"][1] == {
        "name": "Terrn",
        "code": "10",
        "level": 2,
        "parentPath": f'/{data["typeCodeElements"][0]["id"]}',
        "id": data["typeCodeElements"][1]["id"],
    }
