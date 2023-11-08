import base64
import io
from typing import Optional

import pandas as pd
import strawberry
from lcacollect_config.context import get_session
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from sqlalchemy.orm import selectinload
from sqlmodel import select
from strawberry.types import Info

import models.typecode as models_type_code
from schema.inputs import TypeCodeElementFilters, TypeCodeFilters


@strawberry.type
class GraphQLTypeCodeElement:
    id: str
    code: str
    name: str
    level: int
    parent_path: str  # "/parents_parent_id/parent_id" or "/" for no parent

    @strawberry.field
    async def parent_code(self, info: Info) -> str:
        session = info.context.get("session")
        path = list(filter(None, self.parent_path.split("/")))
        parent_code = "/"
        if path:
            if self.level == 2:
                parent = await session.get(models_type_code.TypeCodeElement, path[-1])
                parent_code = f"/{parent.code}"
            if self.level == 3:
                parent1 = await session.get(models_type_code.TypeCodeElement, path[0])
                parent2 = await session.get(models_type_code.TypeCodeElement, path[1])
                parent_code = f"/{parent1.code}/{parent2.code}"
        return parent_code


@strawberry.type
class GraphQLTypeCode:
    id: str
    name: str
    elements: list[GraphQLTypeCodeElement]


async def query_type_code_elements(
    info: Info, filters: TypeCodeElementFilters | None = None
) -> list[GraphQLTypeCodeElement]:
    """Get typeCodeElements"""

    session = get_session(info)

    query = select(models_type_code.TypeCodeElement)
    if filters:
        query = filter_model_query(models_type_code.TypeCodeElement, filters, query=query)

    type_code_elements = await session.exec(query)

    return type_code_elements.all()


async def query_type_codes(info: Info, filters: TypeCodeFilters | None = None) -> list[GraphQLTypeCode]:
    """Get Type Codes"""

    session = get_session(info)

    query = select(models_type_code.TypeCode)

    if filters:
        query = filter_model_query(models_type_code.TypeCode, filters, query=query)
    if category_field := [field for field in info.selected_fields if field.name == "typeCodes"]:
        if [field for field in category_field[0].selections if field.name == "elements"]:
            query = query.options(selectinload(models_type_code.TypeCode.elements))

    type_codes = await session.exec(query)

    return type_codes.all()


async def create_type_code_element(
    info: Info, name: str, code: str, level: int, parent_path: str = "/"
) -> GraphQLTypeCodeElement:
    """Add a new typeCodeElement"""
    session = get_session(info)

    type_code_element = models_type_code.TypeCodeElement(
        code=code,
        name=name,
        level=level,
        parent_path=parent_path,
    )

    session.add(type_code_element)
    await session.commit()
    await session.refresh(type_code_element)

    return type_code_element


async def create_type_code_element_from_source(info: Info, file: str, name: str) -> str:
    """Add a new typeCodeElement from csv file"""
    session = get_session(info)
    data = base64.b64decode(file).decode("utf-8")

    def _add_type_code(dataf: pd.DataFrame, level: int, code_ids: dict[str, str], type_code_id: str):
        for _index, row in dataf.iterrows():
            path = list(filter(None, row.get("parentPath", "/").split("/")))
            formatted_path = "/"
            try:
                if level == 2:
                    formatted_path = f"/{code_ids[path[0]]}"
                if level == 3:
                    formatted_path = f"/{code_ids[path[0]]}/{code_ids[path[1]]}"
            except (KeyError, IndexError):
                return

            type_code_element = models_type_code.TypeCodeElement(
                name=row.get("Name"),
                code=row.get("Code"),
                level=row.get("Level"),
                parent_path=formatted_path,
                typecode_id=type_code_id,
            )
            code_ids.update({type_code_element.code: type_code_element.id})
            session.add(type_code_element)

    type_code = models_type_code.TypeCode(name=name)
    session.add(type_code)

    with io.StringIO(data) as csv_file:
        df = pd.read_csv(csv_file, sep=",")
        code_ids = {}

        df_level1 = df[df.get("Level") == 1]
        _add_type_code(df_level1, 1, code_ids, type_code.id)

        df_level2 = df[df.get("Level") == 2]
        _add_type_code(df_level2, 2, code_ids, type_code.id)

        df_level3 = df[df.get("Level") == 3]
        _add_type_code(df_level3, 3, code_ids, type_code.id)

    await session.commit()

    return "uploaded"


async def update_type_code_element(
    info: Info,
    id: str,
    name: Optional[str] = None,
    level: Optional[int] = None,
    code: Optional[str] = None,
    parent_path: Optional[str] = "/",
) -> GraphQLTypeCodeElement:
    """update typeCodeElement"""
    session = get_session(info)

    type_code_element = await session.get(models_type_code.TypeCodeElement, id)
    if not type_code_element:
        raise DatabaseItemNotFound(f"Could not find TypeCodeElement with id: {id}.")

    kwargs = {"name": name, "level": level, "parent_path": parent_path, "code": code}
    for key, value in kwargs.items():
        if value is not None:
            setattr(type_code_element, key, value)

    session.add(type_code_element)

    await session.commit()
    await session.refresh(type_code_element)

    return type_code_element


async def delete_type_code_element(info: Info, id: str) -> str:
    """Delete a TypeCodeElement"""

    session = get_session(info)

    type_code_element = await session.get(models_type_code.TypeCodeElement, id)

    await session.delete(type_code_element)
    await session.commit()
    return type_code_element
