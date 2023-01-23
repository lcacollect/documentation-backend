from typing import Callable

import pytest
from httpx import AsyncClient

from core.config import settings
from schema.source import ProjectSourceType


@pytest.mark.asyncio
async def test_project_sources_query(
    client: AsyncClient,
    project_sources,
    member_mocker,
    project_exists_mock,
    get_response: Callable,
):

    query = """
        query($projectId: String!) {
            projectSources(projectId: $projectId) {
                name
                projectId
                metaFields
                dataId
            }
        }
    """
    variables = {"projectId": "0"}

    data = await get_response(client, query, variables=variables)
    assert data["projectSources"][0] == {
        "name": f"Source 0",
        "projectId": f"0",
        "metaFields": dict(speckle_url="speckle.arkitema.com"),
        "dataId": "21b253d478",
    }


async def test_project_sources_query_filters(
    client: AsyncClient,
    project_sources,
    member_mocker,
    project_exists_mock,
    get_response: Callable,
):

    query = """
        query($projectId: String!, $name: String!) {
            projectSources(projectId: $projectId, filters: {name: {equal: $name}}) {
                name
                projectId
                metaFields
                dataId
            }
        }
    """
    variables = {"projectId": "1", "name": "Source 1"}

    data = await get_response(client, query, variables=variables)
    assert data["projectSources"][0] == {
        "name": f"Source 1",
        "projectId": f"1",
        "metaFields": dict(speckle_url="speckle.arkitema.com"),
        "dataId": "21b253d478",
    }


async def test_add_file_source_mutation(
    client: AsyncClient,
    project_sources,
    member_mocker,
    blob_client_mock_async,
    project_exists_mock,
    get_response: Callable,
):
    query = f"""
        mutation {{
            addProjectSource(
                projectId: "10"
                type: CSV
                file: "aW0gYSBmaWxlLCBhIGNzdiBmaWxl"
                name: "some_name"
            ) {{
                projectId
                type
                dataId
                name
                authorId
                metaFields
                fileUrl
            }}
        }}
    """

    data = await get_response(client, query)
    assert data["addProjectSource"] == {
        "projectId": "10",
        "type": f"{ProjectSourceType.CSV.name}",
        "dataId": "test/ba/ef/70c78b30e27266c4f5368bfb0938a03a17870355fd1558ca36ec45ddf851",
        "name": "some_name",
        "metaFields": {"url": "PLACEHOLDER/PALCEHOLDER"},
        "fileUrl": "PLACEHOLDER/PALCEHOLDER/test/ba/ef/70c78b30e27266c4f5368bfb0938a03a17870355fd1558ca36ec45ddf851",
        "authorId": "someid0",
    }


async def test_add_speckle_source_mutation(
    client: AsyncClient,
    project_sources,
    member_mocker,
    project_exists_mock,
    get_response: Callable,
):
    query = f"""
        mutation {{
            addProjectSource(
                projectId: "10"
                type: SPECKLE
                dataId: "21b253d478"
                name: "some_name"
                speckleUrl: "speckle.arkitema.com"
            ) {{
                projectId
                type
                dataId
                name
            }}  
        }}
    """

    data = await get_response(client, query)
    assert data["addProjectSource"] == {
        "projectId": "10",
        "type": "SPECKLE",
        "dataId": "21b253d478",
        "name": "some_name",
    }


async def test_update_project_source_mutation(
    client: AsyncClient,
    project_sources,
    member_mocker,
    blob_client_mock_async,
    get_response: Callable,
):
    query = """
        mutation(
            $id: String!
            $name: String
            $type: ProjectSourceType!
            $dataId: String
            $file: String
        ) {
            updateProjectSource(
                id: $id
                dataId: $dataId
                type: $type
                name: $name
                file: $file
            ) {
                projectId
                type
                dataId
                name
            }
        }
    """

    expected_source_id = "test/ba/ef/70c78b30e27266c4f5368bfb0938a03a17870355fd1558ca36ec45ddf851"

    variables = {
        "id": project_sources[0].id,
        "name": "Modified Project",
        "file": "aW0gYSBmaWxlLCBhIGNzdiBmaWxl",
        "type": "CSV",
    }

    data = await get_response(client, query, variables=variables)
    assert data["updateProjectSource"] == {
        "projectId": "0",
        "type": ProjectSourceType.CSV.name,
        "dataId": expected_source_id,
        "name": "Modified Project",
    }


async def test_delete_project_source_mutation(
    client: AsyncClient, project_sources, member_mocker, get_response: Callable
):
    # FIXME: this test for absence of errors, not correct behaviour
    query = """
        mutation($id: String!) {
            deleteProjectSource(id: $id) 
        }
    """
    variables = {
        "id": project_sources[0].id,
    }

    assert await get_response(client, query, variables=variables)
