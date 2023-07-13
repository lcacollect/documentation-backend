from sqlalchemy.orm import selectinload
from sqlmodel import select

import models.reporting_schema as models_schema
import models.schema_category as models_category
import models.schema_element as models_element

from .lcabyg.models import Edge, Entity, Node


async def query_for_lca_byg_export(reporting_schema_id: str, session) -> list[models_category.SchemaCategory]:
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


def aggregate_lcabyg_models(
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
