from sqlalchemy.orm import selectinload
from sqlmodel import select

import models.reporting_schema as models_schema
import models.reporting_schema as models_reporting
import models.schema_category as models_category
import models.schema_element as models_element

from .lcabyg.edges import create_edge
from .lcabyg.models import Entity
from .lcabyg.nodes import create_node
from .utils import query_assemblies_for_export, query_project_for_export


async def query_for_lca_byg_export(
    reporting_schema_id: str, session, token: str
) -> tuple[list[models_category.SchemaCategory], list[dict] | None]:
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
    schema_categories = (await session.exec(query)).all()
    reporting_schema = schema_categories[0].reporting_schema
    assemblies = await query_assemblies_for_export(reporting_schema.project_id, token)

    return schema_categories, assemblies


def aggregate_lcabyg_models(
    schema_categories: list[models_schema.SchemaCategory],
    assemblies: list[dict],
) -> list[Entity]:
    """
    Return list of Edges and Nodes from schema.
    Edges from GenDK to LCAByg Elements and Constructions are automatically inferred from the database.
    """

    entity_list = []
    for category in schema_categories:
        if category.elements == []:  # pragma: no branch
            continue
        category_node = create_node(category)
        entity_list.extend([category_node, create_edge(category_node)])

        for element in category.elements:
            element_node = create_node(element)

            entity_list.extend([element_node, create_edge(element_node, category_node), create_edge(element_node)])

            if element.assembly_id:
                for assembly in assemblies:
                    if assembly["id"] == element.assembly_id:
                        for layer in assembly.get("layers", []):
                            layer_node = create_node(layer)
                            entity_list.extend([layer_node, create_edge(layer_node, element_node)])
                            for phase in ["A1to3", "C3", "C4", "D"]:
                                phase_node = create_node((layer, phase))
                                entity_list.extend(
                                    [phase_node, create_edge(phase_node, layer_node), create_edge(phase_node)]  # ])
                                )

    return entity_list
