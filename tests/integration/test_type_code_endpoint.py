from typing import Callable

import pytest
from httpx import AsyncClient
import base64

@pytest.mark.asyncio
async def test_get_type_code_elements_not_admin(client: AsyncClient, type_code_elements, get_response: Callable):
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}
    
    with pytest.raises(AssertionError) as excinfo:  
        await get_response(client, query, variables=variables)
        
    assert 'User is not an admin' in str(excinfo.value)

@pytest.mark.asyncio
async def test_get_type_code_elements(client: AsyncClient, type_code_elements, is_admin_mock, get_response: Callable):
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 4
    assert data["typeCodeElements"][0] == {
        "name": "Name 0",
        "code": "Code 0",
        "level": 0,
    }


@pytest.mark.asyncio
async def test_add_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 0
    
    query = """
        mutation ($name: String!, $code: String!, $level: Int!){
            createTypeCodeElement(name: $name, code: $code, level: $level) {
                name
                code
                level
            }
        }
    """
    variables = {'name': 'test', 'code': 'test', 'level': 1}
    data = await get_response(client, query, variables=variables)
    
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 1
    assert data["typeCodeElements"][0] == {
        "name": "test",
        "code": "test",
        "level": 1,
    }
    
    
@pytest.mark.asyncio
async def test_update_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 0
    
    query = """
        mutation ($name: String!, $code: String!, $level: Int!){
            createTypeCodeElement(name: $name, code: $code, level: $level) {
                id
            }
        }
    """
    variables = {'name': 'test', 'code': 'test', 'level': 1}
    data = await get_response(client, query, variables=variables)
    query = """
        mutation ($id: String!, $name: String!){
            updateTypeCodeElement(id: $id, name: $name) {
                name
                code
                level
            }
        }
    """
    variables = {'id': data["createTypeCodeElement"]["id"], 'name': 'test2'}
    data = await get_response(client, query, variables=variables)
    
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 1
    assert data["typeCodeElements"][0] == {
        "name": "test2",
        "code": "test",
        "level": 1,
    }

@pytest.mark.asyncio
async def test_delete_type_code_elements(client: AsyncClient, is_admin_mock, get_response: Callable):
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 0
    
    query = """
        mutation ($name: String!, $code: String!, $level: Int!){
            createTypeCodeElement(name: $name, code: $code, level: $level) {
                id
            }
        }
    """
    variables = {'name': 'test', 'code': 'test', 'level': 1}
    data = await get_response(client, query, variables=variables)
    
    query = """
        mutation ($id: String!){
            deleteTypeCodeElement(id: $id)
        }
    """
    variables = {'id': data["createTypeCodeElement"]["id"]}
    data = await get_response(client, query, variables=variables)
    
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 0


@pytest.mark.asyncio
async def test_add_type_code_elements_from_source(client: AsyncClient, is_admin_mock, datafix_dir, get_response: Callable):
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 0
    
    query = """
        mutation ($file: String!){
            createTypeCodeElementFromSource(file: $file) {
                name
                code
                level
            }
        }
    """
    with open(datafix_dir / "type_code_elements.csv", "rb") as file:
        encoded_file = base64.b64encode((file.read())).decode("utf-8")
    
    variables = {'file': encoded_file}
    data = await get_response(client, query, variables=variables)
    
    query = """
        query ($id: String, $name: String, $code: String){
            typeCodeElements(id: $id, name: $name, code: $code) {
                name
                code
                level
            }
        }
    """
    variables = {'id': None, 'name': None, 'code': None}

    data = await get_response(client, query, variables=variables)
    assert len(data["typeCodeElements"]) == 2
    assert data["typeCodeElements"][0] == {
        "name": "Bygningsbasis",
        "code": "1",
        "level": 1,
    }
    