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
