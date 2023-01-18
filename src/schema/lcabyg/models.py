"""Module for mapping SchemaElement and SchemaCategory objects to LCAByg edges and nodes."""
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from lcacollect_config.formatting import string_uuid

from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement

from .utilities import CATEGORY_RESOLVERS, EntityTypes, Units

logger = logging.getLogger(__name__)


class Entity(ABC):  # pragma: no cover
    """Parent class of LCAByg Node and Edge."""

    @abstractmethod
    def as_dict(self) -> dict:
        """Return self in dict form."""
        pass

    def _as_json(self) -> str:
        """Return self in json form."""
        return json.dumps(self.as_dict(), indent=4)

    def __str__(self):
        return self._as_json()

    def __repr__(self):
        try:
            return f'{self.__class__.__name__}("{self.name}")'
        except AttributeError as e:
            return e("__repr__ was called from abstract base class.")


class Node(Entity):
    """LCAByg node model."""

    def __init__(self, entity: SchemaCategory | SchemaElement) -> None:
        self.amount = getattr(entity, "quantity", None)
        self.comment = entity.description or ""
        self.element_category_id = self._resolve_category_name(entity)
        self.id = entity.id
        self.locked = False
        self.name = entity.name
        self.source = "User"
        self.type = self._get_type(entity)

        valid_units = set([e.value for e in Units if e is not Units.NONE])
        if not hasattr(entity, "unit") or entity.unit.upper() == Units.NONE.value.upper():
            # Turn to default if unit not given or unit is "Pcs" (case insensitive)
            self.unit = Units.NONE.value
        elif entity.unit.upper() in valid_units:
            # Get unit from entity if unit is valid (case insensitive)
            self.unit = entity.unit.upper()
        else:
            raise ValueError(f"Expected unit to be one of {valid_units} but got '{self.unit}'.")

    @staticmethod
    def _resolve_category_name(entity: SchemaCategory | SchemaElement) -> str:
        """Extract reporting schema type, resolve category names."""
        if isinstance(entity, SchemaCategory):
            schema_type = entity.reporting_schema.name
        elif isinstance(entity, SchemaElement):
            schema_type = entity.schema_category.reporting_schema.name
        else:
            schema_type = "BIM7AA"

        resolver = CATEGORY_RESOLVERS.get(schema_type)
        if resolver is None:
            logger.error(
                f"Resolver for schema type {schema_type} is undefined."
                "Setting element supercategory and category to 'Other'."
            )
            return "069983d0-d08b-405b-b816-d28ca9648956"

        return resolver(entity)

    @staticmethod
    def _get_type(entity: SchemaCategory | SchemaElement) -> Enum:
        # NOTE: Mostly a placeholder for now
        """Get LCAbyg type based on entity type."""
        if isinstance(entity, SchemaElement):
            return EntityTypes.CONSTRUCTION
        return EntityTypes.ELEMENT

    def as_dict(self) -> dict:

        if self.type is EntityTypes.ELEMENT:
            self_dict = {
                "Node": {
                    self.type.value: {
                        "id": self.id,
                        "name": {
                            "Danish": self.name,
                            "English": self.name,
                            "German": self.name,
                        },
                        "active": True,
                        "comment": self.comment,
                        "enabled": True,
                        "source": self.source,
                    }
                }
            }
        elif self.type is EntityTypes.CONSTRUCTION:
            self_dict = {
                "Node": {
                    self.type.value: {
                        "id": self.id,
                        "name": {
                            "Danish": self.name,
                            "English": self.name,
                            "German": self.name,
                        },
                        "comment": self.comment,
                        "layer": 1,
                        "locked": True,
                        "source": self.source,
                        "unit": self.unit,
                    }
                }
            }

        return self_dict


class Edge(Entity):
    """LCAByg edge model."""

    def __init__(self, child: Node, parent: Optional[Node] = None):
        self.amount = child.amount
        self.child_id = child.id
        self.id = string_uuid()
        if parent is not None:
            self.name = f"{parent.type.value}To{child.type.value}"
            self.parent_id = parent.id
        else:
            # NOTE: If only one Node is passed, create a link between the node and GenDK
            self.name = f"CategoryTo{child.type.value}"
            self.parent_id = child.element_category_id

    def as_dict(self) -> dict:
        if self.name == "ElementToConstruction":
            meta = {
                "amount": self.amount or 0,
                "enabled": True,
                "id": self.id,
            }
        elif self.name == "CategoryToConstruction":
            meta = {
                "id": self.id,
                "layers": [1],
            }
        elif self.name == "CategoryToElement":
            meta = {
                "enabled": True,
                "id": self.id,
            }

        self_dict = {
            "Edge": [
                {self.name: meta},
                self.parent_id,
                self.child_id,
            ]
        }
        return self_dict
