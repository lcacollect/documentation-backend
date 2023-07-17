import json
from pathlib import Path

import pytest

from logic.export.lcabyg.edges import Edge, create_edge
from logic.export.lcabyg.nodes import ConstructionNode, ElementNode, create_node
from logic.export.lcabyg.utilities import _bim7aa_to_gendk_dict
from logic.export.to_lcabyg import aggregate_lcabyg_models
from models.schema_category import SchemaCategory


@pytest.mark.asyncio
async def test_lcabyg_category_node(category: SchemaCategory):
    """Test LCAByg node representing a SchemaCategory."""
    node = ElementNode(category)
    assert node.element_category_id == "10a52123-48d7-466a-9622-d463511a6df0"  # GenDK category ID
    node_dict = node.as_dict()
    assert node_dict == {
        "Node": {
            "Element": {
                "id": category.id,
                "name": {
                    "Danish": category.name,
                    "English": category.name,
                    "German": category.name,
                },
                "active": True,
                "comment": category.description,
                "enabled": True,
                "source": "User",
            }
        }
    }


@pytest.mark.asyncio
async def test_lcabyg_element_node(category: SchemaCategory):
    """Test LCAByg node representing a SchemaCategory."""
    element = category.elements[0]
    node = create_node(element)
    node_dict = node.as_dict()
    assert node_dict == {
        "Node": {
            "Construction": {
                "id": element.id,
                "name": {
                    "Danish": element.name,
                    "English": element.name,
                    "German": element.name,
                },
                "comment": element.description,
                "layer": 1,
                "locked": True,
                "source": "User",
                "unit": "M3",
            }
        }
    }


@pytest.mark.asyncio
async def test_lcabyg_element_to_construction_edge(category: SchemaCategory):
    """Test edge between element node and construction node."""
    category_node = ElementNode(category)
    element_node = ConstructionNode(category.elements[0])
    edge = create_edge(element_node, category_node)
    edge_dict = edge.as_dict()

    assert edge_dict == {
        "Edge": [
            {
                "ElementToConstruction": {
                    "amount": category.elements[0].quantity,
                    "enabled": True,
                    "id": edge.id,
                }
            },
            category.id,
            category.elements[0].id,
        ]
    }


@pytest.mark.asyncio
async def test_lcabyg_category_to_construction_edge(category: SchemaCategory):
    """Test edge between GenDK category and construction node."""
    element_node = ConstructionNode(category.elements[0])
    edge = create_edge(element_node)
    edge_dict = edge.as_dict()

    assert edge_dict == {
        "Edge": [
            {
                "CategoryToConstruction": {
                    "id": edge.id,
                    "layers": [1],
                }
            },
            _bim7aa_to_gendk_dict["211"],
            category.elements[0].id,
        ]
    }


@pytest.mark.asyncio
async def test_lcabyg_category_to_element_edge(category: SchemaCategory):
    """Test edge between GenDK category and element node."""
    category_node = create_node(category)
    edge = create_edge(category_node)
    edge_dict = edge.as_dict()

    assert edge_dict == {
        "Edge": [
            {
                "CategoryToElement": {
                    "enabled": True,
                    "id": edge.id,
                }
            },
            _bim7aa_to_gendk_dict["211"],
            category.id,
        ]
    }


@pytest.mark.asyncio
async def test_aggregate_lcabyg_models(datafix_dir, category: SchemaCategory):
    project = json.loads((datafix_dir / "project_export.json").read_text())["data"]["projects"][0]
    assemblies = json.loads((datafix_dir / "assembly_export.json").read_text())["data"]["assemblies"]

    lcabyg_data = aggregate_lcabyg_models([category], assemblies)
    assert lcabyg_data