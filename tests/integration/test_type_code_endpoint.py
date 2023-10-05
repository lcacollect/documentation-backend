import base64
from typing import Callable

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_type_code_elements_not_admin(client: AsyncClient, type_code_elements, get_response: Callable):
    query = """
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                name
                level
                parentPath
            }
        }
    """
    variables = {"id": None, "name": None}

    with pytest.raises(AssertionError) as excinfo:
        await get_response(client, query, variables=variables)

    assert "User is not an admin" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_type_code_elements(client: AsyncClient, type_code_elements, is_admin_mock, get_response: Callable):
    query = """
        query {
            typeCodeElements{
                id
                name
                level
                parentPath
            }
        }
    """

    data = await get_response(client, query)
    assert len(data["typeCodeElements"]) == 4
    assert data["typeCodeElements"][0] == {
        "id": "Code 0",
        "name": "Name 0",
        "parentPath": "/",
        "level": 0,
    }


@pytest.mark.asyncio
async def test_add_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                name
                level
            }
        }
    """
    variables = {"id": None, "name": None}

    data = await get_response(client, query, variables=variables)
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
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                id
                name
                parentPath
                level
            }
        }
    """
    variables = {"id": None, "name": None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 1
    assert data["typeCodeElements"][0] == {"name": "test", "id": "test", "level": 1, "parentPath": "/"}


@pytest.mark.asyncio
async def test_update_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                name
                level
            }
        }
    """
    variables = {"id": None, "name": None}

    data = await get_response(client, query, variables=variables)
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
        mutation ($id: String!, $name: String!){
            updateTypeCodeElement(id: $id, name: $name) {
                name
                level
            }
        }
    """
    variables = {"id": data["createTypeCodeElement"]["id"], "name": "test2"}
    data = await get_response(client, query, variables=variables)

    query = """
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                name
                id
                level
            }
        }
    """
    variables = {"id": None, "name": None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 1
    assert data["typeCodeElements"][0] == {
        "name": "test2",
        "id": "test",
        "level": 1,
    }


@pytest.mark.asyncio
async def test_delete_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                name
                level
            }
        }
    """
    variables = {"id": None, "name": None}

    data = await get_response(client, query, variables=variables)
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
    data = await get_response(client, query, variables=variables)

    query = """
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                name
                level
            }
        }
    """
    variables = {"id": None, "name": None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 0


@pytest.mark.asyncio
async def test_add_type_code_elements_from_source(
    client: AsyncClient, is_admin_mock, datafix_dir, get_response: Callable
):
    query = """
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                name
                level
            }
        }
    """
    variables = {"id": None, "name": None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 0

    query = """
        mutation ($file: String!){
            createTypeCodeElementFromSource(file: $file) {
                id
            }
        }
    """
    with open(datafix_dir / "type_code_elements.csv", "rb") as file:
        encoded_file = base64.b64encode((file.read())).decode("utf-8")

    variables = {"file": encoded_file}
    data = await get_response(client, query, variables=variables)

    query = """
        query ($id: String, $name: String){
            typeCodeElements(id: $id, name: $name) {
                id
                name
                level
                parentPath
            }
        }
    """
    variables = {"id": None, "name": None}

    data = await get_response(client, query, variables=variables)

    assert len(data["typeCodeElements"]) == 2
    assert data["typeCodeElements"][1] == {"name": "Terrn", "id": "10", "level": 2, "parentPath": "/1/10"}
