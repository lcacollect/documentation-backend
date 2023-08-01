import base64
import json
import io
import codecs
import csv
from enum import Enum

import strawberry
from lcacollect_config.context import get_session
from sqlalchemy.orm import selectinload
from sqlmodel import select
from strawberry.types import Info

import models.reporting_schema as models_schema
import models.schema_category as models_category
import models.schema_element as models_element

from .lcabyg.models import Edge, Entity, Node

# TODO: extract class and subclass as BIM7AA categories when exporting to CSV


@strawberry.enum(name="exportFormat")
class ExportFormat(Enum):
    """Available export formats."""

    LCABYG = "lcayg"
    CSV = "csv"


async def export_reporting_schema_mutation(info: Info, reporting_schema_id: str, export_format: ExportFormat) -> str:
    """Resolver for exporting the database contents as a base64 encoded string."""

    session = get_session(info)
    if export_format is ExportFormat.LCABYG:
        schema_categories = await _query_for_lca_byg_export(reporting_schema_id, session)
        entity_list = _aggregate_lcabyg_models(schema_categories)
        data = json.dumps([entity.as_dict() for entity in entity_list], indent=4)

    elif export_format is ExportFormat.CSV:
        schema_categories = await _query_for_csv_export(reporting_schema_id, session)
        data = _generate_csv_schema(schema_categories)

    else:
        raise NotImplementedError

    return str(base64.b64encode(data.encode("utf-8-sig")), "utf-8")


async def _query_for_lca_byg_export(reporting_schema_id: str, session) -> list[models_category.SchemaCategory]:
    """Query the database for SchemaCategories and the required attributes for LCAByg export."""

    query = (
        select(models_schema.SchemaCategory)
        .where(models_category.SchemaCategory.reporting_schema_id == reporting_schema_id)
        .options(selectinload(models_schema.SchemaCategory.reporting_schema))
        .options(
            selectinload(models_category.SchemaCategory.elements).options(
                selectinload(models_element.SchemaElement.schema_category)
            )
        )
    )
    schema_categories = await session.exec(query)
    return schema_categories.all()


def _aggregate_lcabyg_models(
    schema_categories: list[models_category.SchemaCategory],
) -> list[Entity]:
    """
    Return list of Edges and Nodes from schema.
    Edges from GenDK to LCAByg Elements and Constructions are automatically inferred from the database.
    """

    entity_list = []
    for category in schema_categories:
        # TODO: set up test case where there is a SchemaCategory with no elements and asser that it does not
        # TODO: appear in the .json
        if category.elements == []:  # pragma: no branch
            continue
        category_node = Node(category)
        entity_list.extend([category_node, Edge(category_node)])

        for element in category.elements:
            element_node = Node(element)

            entity_list.extend([element_node, Edge(element_node, category_node), Edge(element_node)])
    return entity_list


async def _query_for_csv_export(reporting_schema_id: str, session) -> list[models_category.SchemaCategory]:
    """Query the database for SchemaCategories and the required attributes for CSV export."""

    query = (
        select(models_schema.SchemaCategory)
        .where(models_category.SchemaCategory.reporting_schema_id == reporting_schema_id)
        .options(selectinload(models_schema.SchemaCategory.reporting_schema))
        .options(
            selectinload(models_category.SchemaCategory.elements)
            .options(selectinload(models_element.SchemaElement.schema_category))
            .options(selectinload(models_element.SchemaElement.source))
        )
    )
    schema_categories = await session.exec(query)
    return schema_categories.all()


def _generate_csv_schema(schema_categories: list[models_schema.SchemaCategory]) -> str:
    """Generate a CSV string of the database contents."""

    csv_io = io.StringIO("", newline="")
    fields = ["class", "name", "source", "quantity", "unit", "description"]

    wrapper = csv.DictWriter(csv_io, fieldnames=fields, delimiter=";", quoting=csv.QUOTE_NONNUMERIC)

    # Generate the header row
    wrapper.writeheader()
    # Extract field values from SchemaElements
    for category in schema_categories:
        # ?: Create extra line for category here?
        for element in category.elements:
            values = {
                "class": element.schema_category.name,
                "name": element.name,
                "source": element.source.name if element.source else "Typed in",
                "quantity": element.quantity,
                "unit": element.unit,
                "description": element.description,
            }
            wrapper.writerow(values)
    return csv_io.getvalue()
