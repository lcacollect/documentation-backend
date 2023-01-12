import pytest

from models.schema_category import SchemaCategory
from schema.lcabyg.models import Edge, Node
from schema.lcabyg.utilities import _bim7aa_to_gendk_dict


@pytest.mark.asyncio
async def test_lcabyg_category_node(category: SchemaCategory):
    """Test LCAByg node representing a SchemaCategory."""
    node = Node(category)
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
    node = Node(element)
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
    category_node = Node(category)
    element_node = Node(category.elements[0])
    edge = Edge(element_node, category_node)
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
    element_node = Node(category.elements[0])
    edge = Edge(element_node)
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
    category_node = Node(category)
    edge = Edge(category_node)
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
