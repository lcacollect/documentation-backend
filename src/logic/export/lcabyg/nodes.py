import logging

from lcacollect_config.formatting import string_uuid

from logic.export.lcabyg.models import Entity
from logic.export.lcabyg.utilities import EntityTypes, Units, CATEGORY_RESOLVERS
from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement

logger = logging.getLogger(__name__)


def create_node(entity: SchemaCategory | SchemaElement | dict | tuple[dict, str]) -> "Node":
    if isinstance(entity, SchemaElement):
        return ConstructionNode(entity)
    elif isinstance(entity, SchemaCategory):
        return ElementNode(entity)
    elif isinstance(entity, dict):
        return ProductNode(entity)
    elif isinstance(entity, tuple):
        return StageNode(*entity)
    else:
        raise NotImplementedError(f"Type {type(entity)} is not implemented.")


class Node(Entity):
    """LCAByg node model."""

    def __init__(self):
        self.locked = False
        self.source = "User"

    def as_dict(self) -> dict:
        raise NotImplementedError


class ClassNode(Node):
    def __init__(self, entity: SchemaCategory | SchemaElement):
        self.id = entity.id
        self.name = entity.name
        self.comment = entity.description
        self.unit = self._get_unit(entity)
        self.element_category_id = self._resolve_category_name(entity)
        super().__init__()

    @staticmethod
    def _get_unit(entity: SchemaCategory | SchemaElement | dict) -> str | None:
        """Get unit from entity."""

        valid_units = set([e.value for e in Units if e is not Units.NONE])
        if not hasattr(entity, "unit") or entity.unit.upper() == Units.NONE.value.upper():
            # Turn to default if unit not given or unit is "Pcs" (case insensitive)
            return Units.NONE.value
        elif entity.unit.upper() in valid_units:
            # Get unit from entity if unit is valid (case insensitive)
            return entity.unit.upper()
        else:
            raise ValueError(f"Expected unit to be one of {valid_units} but got '{entity.unit.upper()}'.")

    @staticmethod
    def _resolve_category_name(entity: SchemaCategory | SchemaElement) -> str | None:
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


class DictNode(Node):

    def __init__(self, entity: dict):
        self.id = entity.get("id")
        self.name = entity.get("name")
        self.comment = entity.get("description", "") or ""
        super().__init__()


class ElementNode(ClassNode):

    def __init__(self, entity: SchemaCategory):
        self.type = EntityTypes.ELEMENT
        super().__init__(entity)

    def as_dict(self) -> dict:
        return {
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


class ConstructionNode(ClassNode):
    def __init__(self, entity: SchemaElement):
        self.type = EntityTypes.CONSTRUCTION
        self.amount = entity.quantity
        super().__init__(entity)

    def as_dict(self) -> dict:
        return {
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


class ProductNode(DictNode):
    def __init__(self, entity: dict):
        self.type = EntityTypes.PRODUCT
        self.life_span = entity.get("referenceServiceLife")
        self.amount = entity.get("conversionFactor")
        self.unit = entity.get("epd", {}).get("declaredUnit", "").upper()
        super().__init__(entity)

    def as_dict(self) -> dict:
        return {
            "Node": {
                "Product": {
                    "id": self.id,
                    "name": {
                        "Danish": self.name,
                        "English": self.name,
                        "German": self.name,
                    },
                    "source": self.source,
                    "comment": self.comment,
                    "uncertainty_factor": 1.0,
                    "uncertainty_factor_dgnb": 1.3
                }
            }
        }


class StageNode(DictNode):
    def __init__(self, entity: dict, stage: str):
        epd = entity.get("epd", {})
        epd["id"] = string_uuid()
        self.ser = None
        self.senr = None
        self.per = None
        self.penr = None
        self.adpe = None
        self.ep = None
        self.ap = None
        self.pocp = None
        self.odp = None
        self.gwp = None
        self.adpf = None
        self.type = EntityTypes.STAGE
        self.stage = stage
        self.set_indicators(epd, stage)
        self.data_type = epd.get("subtype")
        self.unit = epd.get("declaredUnit", "").upper()
        self.valid_to = epd.get("validUntil")
        self.mass_factor = self._get_mass_factor(epd)
        self.element_category_id = "f1bca522-df0d-4b74-a5de-cdecc2763d05"
        super().__init__(epd)

    def set_indicators(self, entity: dict, stage: str):
        if stage == "A1to3":
            stage = "a1a3"
        self.gwp = entity.get("gwp", {}).get(stage.lower(), 0) or 0
        self.odp = 0
        self.pocp = 0
        self.ap = 0
        self.ep = 0
        self.adpe = 0
        self.adpf = 0
        self.penr = 0
        self.per = 0
        self.senr = 0
        self.ser = 0

    @staticmethod
    def _get_mass_factor(entity: dict) -> float:
        for conversion in entity.get("conversions"):
            if conversion.get("to") == "kg":
                return conversion.get("value")

    def as_dict(self) -> dict:
        return {
            "Node": {
                "Stage": {
                    "id": self.id,
                    "name": {
                        "Danish": self.name,
                        "English": self.name,
                        "German": self.name,
                    },
                    "comment": self.comment,
                    "source": self.source,
                    "locked": True,
                    "valid_to": self.valid_to,
                    "stage": self.stage,
                    "stage_unit": self.unit,
                    "indicator_unit": self.unit,
                    "stage_factor": 1.0,
                    "mass_factor": self.mass_factor,
                    "indicator_factor": 1.0,
                    "external_source": self.source,
                    "external_id": "",
                    "external_url": "",
                    "external_version": "",
                    "data_type": self.data_type,
                    "indicators": {
                        "GWP": self.gwp,
                        "ODP": self.odp,
                        "POCP": self.pocp,
                        "AP": self.ap,
                        "EP": self.ep,
                        "ADPE": self.adpe,
                        "ADPF": self.adpf,
                        "PENR": self.penr,
                        "PER": self.per,
                        "SENR": self.senr,
                        "SER": self.ser,
                    }
                }
            }
        }
