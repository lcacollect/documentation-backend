import inspect
import sys
from typing import TYPE_CHECKING, Optional

from lcacollect_config.formatting import string_uuid

from logic.export.lcabyg.models import Entity

if TYPE_CHECKING:
    from logic.export.lcabyg.nodes import (
        ConstructionNode,
        ElementNode,
        Node,
        ProductNode,
        StageNode,
    )


def create_edge(child: "Node", parent: Optional["Node"] = None) -> "Edge":
    classes = {key: value for key, value in inspect.getmembers(sys.modules[__name__], inspect.isclass)}
    if parent is not None:
        name = f"{parent.type.value}To{child.type.value}Edge"
        parent_id = parent.id
        edge_class = classes[name]
        return edge_class(child, parent_id)
    else:
        # NOTE: If only one Node is passed, create a link between the node and GenDK
        name = f"CategoryTo{child.type.value}Edge"
        parent_id = child.element_category_id
        edge_class = classes[name]
        return edge_class(child, parent_id)


class Edge(Entity):
    """LCAByg edge model."""

    def __init__(self, child: "Node", parent_id: str):
        self.child_id = child.id
        self.id = string_uuid()
        self.parent_id = parent_id

    def _get_meta_data(self):
        raise NotImplementedError

    def as_dict(self) -> dict:
        self_dict = {
            "Edge": [
                {self.name: self._get_meta_data()},
                self.parent_id,
                self.child_id,
            ]
        }
        return self_dict


class ElementToConstructionEdge(Edge):
    def __init__(self, child: "ConstructionNode", parent_id: str):
        self.name = "ElementToConstruction"
        self.amount = child.amount
        super().__init__(child, parent_id)

    def _get_meta_data(self):
        return {
            "amount": self.amount or 0,
            "enabled": True,
            "id": self.id,
        }


class CategoryToConstructionEdge(Edge):
    def __init__(self, child: "ConstructionNode", parent_id: str):
        self.name = "CategoryToConstruction"
        super().__init__(child, parent_id)

    def _get_meta_data(self):
        return {
            "id": self.id,
            "layers": [1],
        }


class CategoryToElementEdge(Edge):
    def __init__(self, child: "ElementNode", parent_id: str):
        self.name = "CategoryToElement"
        super().__init__(child, parent_id)

    def _get_meta_data(self):
        return {
            "enabled": True,
            "id": self.id,
        }


class ConstructionToProductEdge(Edge):
    def __init__(self, child: "ProductNode", parent_id: str):
        self.name = "ConstructionToProduct"
        self.amount = child.amount
        self.unit = child.unit
        self.life_span = child.life_span
        super().__init__(child, parent_id)

    def _get_meta_data(self):
        return {
            "id": self.id,
            "amount": self.amount or 0,
            "unit": self.unit,
            "lifespan": int(self.life_span),
            "demolition": False,
            "delayed_start": 0,
            "enabled": True,
            "expected_scenarios": [],
        }


class ProductToStageEdge(Edge):
    def __init__(self, child: "StageNode", parent_id: str):
        self.name = "ProductToStage"
        super().__init__(child, parent_id)

    def _get_meta_data(self):
        return {
            "id": self.id,
            "excluded_scenarios": [],
            "enabled": True,
        }


class CategoryToStageEdge(Edge):
    def __init__(self, child: "StageNode", parent_id: str):
        self.name = "CategoryToStage"
        super().__init__(child, parent_id)

    def _get_meta_data(self):
        return self.id
