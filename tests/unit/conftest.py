from pathlib import Path
from typing import List

import pytest
from httpx import AsyncClient
from lcacollect_config.connection import create_postgres_engine
from pytest_alembic.config import Config
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from initial_data.load import load_all
from models.reporting_schema import ReportingSchema
from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement
from models.typecode import TypeCodeElement


@pytest.fixture
def alembic_config():
    """Override this fixture to configure the exact alembic context setup required."""
    yield Config()


@pytest.fixture
def alembic_engine(postgres):
    """Override this fixture to provide pytest-alembic powered tests with a database handle."""
    yield create_postgres_engine(as_async=False)


@pytest.fixture()
async def category(client: AsyncClient, db) -> List[SchemaElement]:
    """Initialise dummy schema category and element."""

    async with AsyncSession(db) as session:
        schema = ReportingSchema(name="BIM7AA")
        typeCodeElement = TypeCodeElement(
            code="211",
            name="Udvendige vægelementer",
            level=1,
        )
        category = SchemaCategory(
            description="Nobody expects the Spanish Inquisition!",
            project_id="123",
            type_code_element_id=typeCodeElement.id,
        )
        element = SchemaElement(
            description="A 5th century oak palisade wall.",
            name="Wall",
            quantity=2500,
            schema_category_id=category.id,
            assembly_id="c95bed36-3cbd-4e8c-9eca-79449557ad76",
            unit="m3",  # LCAByg-incompatible value on purpose. Will be converted to upper case
        )
        category.elements.append(element)
        schema.categories.append(category)
        session.add(typeCodeElement)
        session.add(category)
        session.add(element)
        session.add(schema)
        await session.commit()
        # Load object
        query = (
            select(SchemaCategory)
            .options(selectinload(SchemaCategory.elements).options(selectinload(SchemaElement.schema_category)))
            .options(selectinload(SchemaCategory.reporting_schema))
            .options(selectinload(SchemaCategory.type_code_element))
        )
        schema_categories = (await session.exec(query)).all()
        category = schema_categories[0]

    yield category
