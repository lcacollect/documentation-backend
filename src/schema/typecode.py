import base64
import csv
import io
from typing import Optional

import strawberry
from lcacollect_config.context import get_session
from lcacollect_config.exceptions import DatabaseItemNotFound
from sqlmodel import select
from strawberry.types import Info

import models.typecode as models_type_code


@strawberry.type
class GraphQLTypeCodeElement:
    id: str
    name: str
    code: str
    level: int


async def query_type_code_elements(
    info: Info, id: Optional[str] = None, name: Optional[str] = None, code: Optional[str] = None
) -> list[GraphQLTypeCodeElement]:
    """Get typeCodeElements"""

    session = get_session(info)

    if id:
        query = select(models_type_code.TypeCodeElement).where(models_type_code.TypeCodeElement.id == id)
    elif name:
        query = select(models_type_code.TypeCodeElement).where(models_type_code.TypeCodeElement.name == name)
    elif code:
        query = select(models_type_code.TypeCodeElement).where(models_type_code.TypeCodeElement.code == code)
    else:
        query = select(models_type_code.TypeCodeElement)

    type_code_elements = await session.exec(query)

    return type_code_elements.all()


async def create_type_code_element(info: Info, name: str, code: str, level: int) -> GraphQLTypeCodeElement:
    """Add a new typeCodeElement"""
    session = get_session(info)

    type_code_element = models_type_code.TypeCodeElement(
        name=name,
        code=code,
        level=level,
    )

    session.add(type_code_element)
    await session.commit()
    await session.refresh(type_code_element)

    return type_code_element


async def create_type_code_element_from_source(info: Info, file: str) -> GraphQLTypeCodeElement:
    """Add a new typeCodeElement from csv file"""
    session = get_session(info)
    data = base64.b64decode(file).decode("utf-8")

    with io.StringIO(data) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            row = dict((k.lower(), v) for k, v in row.items())
            type_code_element = models_type_code.TypeCodeElement(
                name=row.get("name"),
                code=row.get("code"),
                level=row.get("level"),
            )

            session.add(type_code_element)

    await session.commit()
    await session.refresh(type_code_element)

    return type_code_element


async def update_type_code_element(
    info: Info, id: str, name: Optional[str] = None, code: Optional[str] = None, level: Optional[int] = None
) -> GraphQLTypeCodeElement:
    """update typeCodeElement"""
    session = get_session(info)

    type_code_element = await session.get(models_type_code.TypeCodeElement, id)
    if not type_code_element:
        raise DatabaseItemNotFound(f"Could not find TypeCodeElement with id: {id}.")

    kwargs = {"name": name, "code": code, "level": level}
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
