from typing import Callable

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models.reporting_schema import ReportingSchema
from models.repository import Repository


@pytest.mark.asyncio
async def test_get_reporting_schemas(
    client: AsyncClient,
    reporting_schemas,
    project_exists_mock,
    member_mocker,
    project_id,
    get_response: Callable,
):
    query = """
        query($projectId: String!) {
            reportingSchemas(projectId: $projectId) {
                name
                projectId
                categories {
                    typeCodeElement {
                        name
                    }
                    elements {
                        name
                    }
                }
            }
        }
    """
    variables = {"projectId": project_id}
    data = await get_response(client, query, variables=variables)
    assert data["reportingSchemas"][0] == {"name": f"Reporting Schema 0", "projectId": project_id, "categories": []}


@pytest.mark.asyncio
async def test_get_reporting_schemas_bad_id(
    client: AsyncClient,
    reporting_schemas,
    project_doesnt_exists_mock,
    mocker,
    get_response: Callable,
):
    mocker.patch("core.federation.get_members", return_value=[])
    query = """
        query($projectId: String!) {
            reportingSchemas(projectId: $projectId) {
                name
                projectId
                categories {
                    typeCodeElement {
                        name
                    }
                    elements {
                        name
                    }
                }
            }
        }
    """
    variables = {"projectId": "1"}

    with pytest.raises(AssertionError):
        await get_response(client, query, variables=variables)


@pytest.mark.asyncio
async def test_get_reporting_schemas_with_filter(
    client: AsyncClient,
    reporting_schemas,
    project_exists_mock,
    member_mocker,
    project_id,
    get_response: Callable,
):
    query = """
        query ($projectId: String!) {
            reportingSchemas(projectId: $projectId, filters: {name: {contains: "0"}}) {
                name
                projectId
            }
        }
    """
    variables = {"projectId": project_id}

    data = await get_response(client, query, variables=variables)
    assert len(data["reportingSchemas"]) == 1
    assert data["reportingSchemas"] == [{"name": reporting_schemas[0].name, "projectId": project_id}]


@pytest.mark.asyncio
async def test_create_reporting_schema(
    client: AsyncClient,
    reporting_schemas,
    schema_templates,
    db,
    member_mocker,
    get_response: Callable,
):
    mutation = """
        mutation($templateId: String!, $projectId: String!) {
            addReportingSchema(name: "Reporting Schema 0", projectId: $projectId, templateId: $templateId) {
                name
                projectId
                id
            }
        }
    """
    variables = {"templateId": schema_templates[0].id, "projectId": "0"}

    data = await get_response(client, mutation, variables=variables)
    assert data["addReportingSchema"] == {
        "name": reporting_schemas[0].name,
        "projectId": "0",
        "id": data["addReportingSchema"]["id"],
    }

    async with AsyncSession(db) as session:
        query = select(Repository)
        repo = await session.exec(query)
        repo = repo.first()

    assert repo
    assert repo.reporting_schema_id == data["addReportingSchema"]["id"]


@pytest.mark.asyncio
async def test_update_reporting_schema(
    client: AsyncClient,
    reporting_schemas,
    project_exists_mock,
    project_id,
    member_mocker,
    get_response: Callable,
):
    query = """
        mutation($id: String! $name: String = null) {
            updateReportingSchema(id: $id, name: $name) {
                name
                projectId
            }
        }
    """
    variables = {"id": reporting_schemas[0].id}
    data = await get_response(client, query, variables=variables)

    assert data["updateReportingSchema"] == {
        "name": reporting_schemas[0].name,
        "projectId": project_id,
    }


@pytest.mark.asyncio
async def test_delete_reporting_schema(
    client: AsyncClient, reporting_schemas, db, member_mocker, get_response: Callable
):
    query = f"""
        mutation {{
            deleteReportingSchema(id: "{reporting_schemas[0].id}")
        }}
    """

    assert await get_response(client, query)

    async with AsyncSession(db) as session:
        query = select(ReportingSchema)
        _schemas = await session.exec(query)
        _schemas = _schemas.all()

    assert len(_schemas) == len(reporting_schemas) - 1


@pytest.mark.asyncio
async def test_create_reporting_schema_from_template(
    client: AsyncClient,
    reporting_schemas,
    schema_templates,
    db,
    member_mocker,
    get_response: Callable,
):
    mutation = """
        mutation($templateId: String!) {
            addReportingSchemaFromTemplate(name: "Reporting Schema 0", projectId: "testID", templateId: $templateId) {
                name
                projectId
                id
            }
        }
    """
    variables = {"templateId": schema_templates[0].id}

    data = await get_response(client, mutation, variables=variables)

    assert data["addReportingSchemaFromTemplate"] == {
        "name": reporting_schemas[0].name,
        "projectId": "testID",
        "id": data["addReportingSchemaFromTemplate"]["id"],
    }

    async with AsyncSession(db) as session:
        query = select(Repository)
        repo = await session.exec(query)
        repo = repo.first()

    assert repo
    assert repo.reporting_schema_id == data["addReportingSchemaFromTemplate"]["id"]
