from typing import Callable

import pytest
from httpx import AsyncClient

from core.config import settings
from core.federation import GraphQLProjectMember


@pytest.mark.asyncio
async def test_get_commits(client: AsyncClient, commits, reporting_schemas, member_mock, get_response: Callable):
    query = """
        query ($reportingSchemaId: String!) {
            commits(reportingSchemaId: $reportingSchemaId, filters: {id: {contains: "-"}}) {
                id
                parentId
                repositoryId
                added
                authorId

            }
        }
    """
    variables = {"reportingSchemaId": f"{reporting_schemas[1].id}"}

    data = await get_response(client, query, variables=variables)
    assert data["commits"] == [
        {
            "id": commits[1].id,
            "parentId": commits[1].parent_id,
            "authorId": commits[1].author_id,
            "repositoryId": commits[1].repository_id,
            "added": commits[1].added.strftime("%Y-%m-%d"),
        }
    ]
