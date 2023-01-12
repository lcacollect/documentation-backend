from typing import Callable
from unittest.mock import Mock

import pytest
from azure.storage.blob import BlobProperties
from httpx import AsyncClient

from core.config import settings
from schema.source import GraphQLProjectSource, ProjectSourceType


@pytest.mark.asyncio
async def test_project_source_files_query(
    client: AsyncClient,
    project_sources: list[GraphQLProjectSource],
    mocker,
    get_response: Callable,
):
    data_id = "test/39/92/3ce5233dbf3400bb9905fdec8fd2355ab15b1ef242b2ef1d2756192d64a0"
    list_blobs_return_value = [BlobProperties(name=data_id)]
    mocker.patch("azure.storage.blob.ContainerClient.list_blobs", return_value=list_blobs_return_value)

    projectSourceFiles = Mock(spec=["data_id", "headers", "rows"])
    projectSourceFiles.data_id = data_id
    projectSourceFiles.headers = ["header1", "header2"]
    projectSourceFiles.rows = [
        {"header1": "header1 - row1", "header2": "header2 - row1"},
        {"header1": "header1 - row2", "header2": "header2 - row2"},
    ]
    mocker.patch(
        "schema.source_file.construct_source_file",
        return_value=projectSourceFiles,
    )

    query = f"""
        query($dataIds: [String!], $type: ProjectSourceType) {{
            projectSourceFiles(dataIds: $dataIds, type: $type) {{
                dataId
                headers
                rows
            }}
        }}
    """
    data_id = project_sources[3].data_id
    variables = {"dataIds": [data_id], "type": ProjectSourceType.CSV.name}

    data = await get_response(client, query, variables=variables)
    source_file = data["projectSourceFiles"][0]
    assert source_file["dataId"] == "test/39/92/3ce5233dbf3400bb9905fdec8fd2355ab15b1ef242b2ef1d2756192d64a0"
    assert len(source_file["headers"]) > 0
    assert len(source_file["dataId"]) > 0
