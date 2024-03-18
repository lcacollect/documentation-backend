import base64
import json
from typing import Callable

import pytest
from httpx import AsyncClient
from lcax.pydantic import LCAxProject
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from logic.export.lcabyg.edges import Edge, create_edge
from logic.export.lcabyg.nodes import Node, create_node
from models.reporting_schema import ReportingSchema
from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement
from models.source import ProjectSource


@pytest.fixture
def mock_uuid(mocker):
    """Mock out the uuid for deterministic testing."""
    mocker.patch("logic.export.lcabyg.models.string_uuid", return_value="test")


@pytest.fixture
@pytest.mark.asyncio
async def expected_entities(mock_uuid, db, schema_elements, schema_categories) -> tuple[Node, Edge]:
    """Generate expected entities."""
    async with AsyncSession(db) as session:
        query = (
            select(SchemaCategory)
            .options(selectinload(SchemaCategory.type_code_element))
            .options(selectinload(SchemaCategory.elements).options(selectinload(SchemaElement.schema_category)))
            .options(selectinload(SchemaCategory.reporting_schema))
        )
        schema_categories = (await session.exec(query)).all()
        category = schema_categories[0]
        element = schema_categories[0].elements[0]
        entity_tuple = (
            category_node := create_node(category),
            element_node := create_node(element),
            create_edge(element_node, category_node),
            create_edge(element_node),
            create_edge(category_node),
        )
    return entity_tuple


@pytest.mark.asyncio
async def test_export_schema_to_lcabyg(
    db,
    client: AsyncClient,
    reporting_schemas: list[ReportingSchema],
    expected_entities: tuple[Node | Edge],
    get_response: Callable,
    query_assemblies_for_export_mock,
):
    query = """
        query ExportReportingSchema($reportingSchemaId: String!, $exportFormat: exportFormat!){
            exportReportingSchema(reportingSchemaId: $reportingSchemaId, exportFormat: $exportFormat)
        }
    """
    variables = {
        "reportingSchemaId": reporting_schemas[0].id,
        "exportFormat": "LCABYG",
    }

    data = await get_response(client, query, variables=variables)
    assert isinstance(data["exportReportingSchema"], str)

    lcabyg_list = json.loads(base64.b64decode(data["exportReportingSchema"]))

    # Test if correct number of entities is returned
    if (a := len(lcabyg_list)) != (b := len(expected_entities)):
        raise AssertionError(f"Expected {b} entities but got {a}.")


@pytest.mark.asyncio
async def test_csv_export(client, db, reporting_schemas, schema_elements, schema_categories):
    query = """
        query ExportReportingSchema($reportingSchemaId: String!, $exportFormat: exportFormat!){
            exportReportingSchema(reportingSchemaId: $reportingSchemaId, exportFormat: $exportFormat)
        }
    """

    async with AsyncSession(db) as session:
        project_source = await session.get(ProjectSource, schema_elements[0].source_id)

    response = await client.post(
        f"{settings.API_STR}/graphql",
        json={
            "query": query,
            "variables": {
                "reportingSchemaId": reporting_schemas[0].id,
                "exportFormat": "CSV",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"]["exportReportingSchema"], str)
    csv_rows = base64.b64decode(data["data"]["exportReportingSchema"])
    csv_rows = csv_rows.decode("utf-8").split("\r\n")

    assert csv_rows[0] == "class;name;source;quantity;unit;description;result"
    element = schema_elements[0]
    expected_data = ";".join(
        [
            str(i)
            for i in (
                "Name 1",
                element.name,
                project_source.name,
                element.quantity,
                element.unit,
                element.description,
                element.total_result,
            )
        ]
    )
    assert csv_rows[1] == expected_data


@pytest.mark.asyncio
async def test_lcax_export(
    client,
    db,
    reporting_schemas,
    schema_elements,
    schema_categories,
    query_project_for_export_mock,
    query_assemblies_for_export_mock,
):
    query = """
        query ExportReportingSchema($reportingSchemaId: String!, $exportFormat: exportFormat!){
            exportReportingSchema(reportingSchemaId: $reportingSchemaId, exportFormat: $exportFormat)
        }
    """

    response = await client.post(
        f"{settings.API_STR}/graphql",
        json={
            "query": query,
            "variables": {
                "reportingSchemaId": reporting_schemas[0].id,
                "exportFormat": "LCAX",
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data.get("errors") is None
    assert isinstance(data["data"]["exportReportingSchema"], str)

    lcax_data = base64.b64decode(data["data"]["exportReportingSchema"]).decode("utf-8")
    assert lcax_data

    lcax_project = LCAxProject(**json.loads(lcax_data))
    assert lcax_project
