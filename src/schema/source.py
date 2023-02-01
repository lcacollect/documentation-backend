import base64
import datetime
import logging
from enum import Enum
from hashlib import sha256
from typing import TYPE_CHECKING, Annotated, Optional

import strawberry
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob.aio import BlobClient
from lcacollect_config.context import get_session, get_user
from lcacollect_config.exceptions import DatabaseItemNotFound
from lcacollect_config.graphql.input_filters import filter_model_query
from specklepy.api.client import SpeckleClient
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from strawberry.scalars import JSON
from strawberry.types import Info

import models.source as models_source
from core.config import settings
from core.validate import authenticate, authenticate_project
from schema.inputs import ProjectSourceFilters

if TYPE_CHECKING:  # pragma: no cover
    from models.source import ProjectSource
    from schema.schema_element import GraphQLSchemaElement

logger = logging.getLogger(__name__)


@strawberry.enum
class ProjectSourceType(Enum):
    CSV = "csv"
    SPECKLE = "speckle"


@strawberry.type
class GraphQLSourceFile:
    headers: list[str]
    rows: JSON


@strawberry.federation.type(keys=["id"])
class GraphQLProjectSource:
    id: strawberry.ID
    type: ProjectSourceType
    data_id: str
    name: str
    project_id: str = strawberry.federation.field(shareable=True)
    meta_fields: JSON
    interpretation: JSON
    author_id: str = strawberry.federation.field(shareable=True)
    updated: datetime.datetime
    elements: list[Annotated["GraphQLSchemaElement", strawberry.lazy("schema.schema_element")]] | None

    @strawberry.field
    def file_url(self) -> str | None:
        if self.type == ProjectSourceType.CSV.value:
            return self.meta_fields.get("url") + "/" + self.data_id

    @strawberry.field
    def data(self: "ProjectSource") -> GraphQLSourceFile | None:
        if self.type == ProjectSourceType.CSV.value:
            headers, rows = self.data
            return GraphQLSourceFile(headers=headers, rows=rows)


async def project_sources_query(
    info: Info, project_id: str, filters: Optional[ProjectSourceFilters] = None
) -> list[GraphQLProjectSource]:
    """Get all sources associated with a project"""

    session = get_session(info)

    query = select(models_source.ProjectSource)
    if project_id:
        query = query.where(models_source.ProjectSource.project_id == project_id)
    if [field for field in info.selected_fields if field.name == "elements"]:
        query = query.options(selectinload(models_source.ProjectSource.elements))

    if filters:
        query = filter_model_query(models_source.ProjectSource, filters, query)

    sources = (await session.exec(query)).all()

    _ = await authenticate(info, project_id or sources[0].project_id)
    await authenticate_project(info, project_id or sources[0].project_id)

    return sources


async def add_project_source_mutation(
    info: Info,
    project_id: str,
    type: ProjectSourceType,
    name: str,
    data_id: str | None = None,
    speckle_url: str | None = None,
    file: str | None = None,
) -> GraphQLProjectSource:

    """Add a Project Source"""

    session = get_session(info)
    user = get_user(info)

    members = await authenticate(info, project_id)
    await authenticate_project(info, project_id)

    project_source = models_source.ProjectSource(
        project_id=project_id,
        type=type.value,
        data_id=data_id,
        name=name,
        interpretation={},
        meta_fields=dict(speckle_url=f"{speckle_url}") if speckle_url else {},
        author_id=user.claims.get("oid"),
    )

    if type == ProjectSourceType.SPECKLE:
        for member in members:
            await invite_members_to_stream(member.email, data_id, project_source.meta_fields.get("speckle_url"))

    if file:
        project_source.data_id = await handle_file_upload(file, project_source)

    session.add(project_source)

    await session.commit()

    return project_source


async def update_project_source_mutation(
    info: Info,
    id: str,
    type: ProjectSourceType | None = None,
    data_id: str | None = None,
    name: str | None = None,
    file: Optional[str] = None,
    meta_fields: Optional[JSON] = None,
    interpretation: Optional[JSON] = None,
    speckle_url: str | None = None,
) -> GraphQLProjectSource:

    """Update a Project Source"""

    session: AsyncSession = info.context.get("session")
    project_source = await session.get(models_source.ProjectSource, id)
    _ = await authenticate(info, project_source.project_id)

    user = info.context.get("user")

    if not project_source:
        raise DatabaseItemNotFound(f"Could not find project source with id: {id}")

    if meta_fields is None:
        meta_fields = {}

    if interpretation is None:
        interpretation = {}

    if file:
        data_id = await handle_file_upload(file, project_source)

    kwargs = {
        "type": type.value if type is not None else None,
        "data_id": data_id,
        "name": name,
        "meta_fields": meta_fields,
        "interpretation": interpretation,
        "author_id": user.claims.get("oid"),
        "updated": datetime.datetime.now(),
    }

    for key, value in kwargs.items():
        if value and key == "meta_fields":
            fields = {**project_source.meta_fields, **value}
            project_source.meta_fields = fields
        if value and key == "interpretation":
            fields = {**project_source.interpretation, **value}
            project_source.interpretation = fields
        elif value:
            setattr(project_source, key, value)

    if speckle_url:
        project_source.meta_fields["speckle_url"] = speckle_url

    session.add(project_source)

    await session.commit()
    await session.refresh(project_source)

    return project_source


async def delete_project_source_mutation(info: Info, id: str) -> str:

    """Delete a project source"""

    session = info.context.get("session")
    source = await session.get(models_source.ProjectSource, id)
    _ = await authenticate(info, source.project_id)
    await session.delete(source)
    await session.commit()
    return id


async def handle_file_upload(file: str, project_source: models_source.ProjectSource) -> str:

    """Handle the source file upload"""

    data = base64.b64decode(file)
    project_source.meta_fields[
        "url"
    ] = f"{settings.STORAGE_ACCOUNT_URL.strip('/')}/{settings.STORAGE_CONTAINER_NAME.strip('/')}"
    return await upload_to_storage_account(data)


async def upload_to_storage_account(data: str | bytes) -> str:

    """
    Upload csv file to Azure Storage Account Blob Container

    Returns:
        Path to the file in blob container.
        Path is constructed as follows:
        `hash/{sha256[:2]}/{hash_str[2:4]}/{hash_str[4:]}`
        where sha256 is sha256 hash of the input string
    """

    if not isinstance(data, bytes):
        data = data.encode()
    hash_str = sha256(data).hexdigest()
    filepath = f"{settings.STORAGE_BASE_PATH}/{hash_str[:2]}/{hash_str[2:4]}/{hash_str[4:]}"

    async with BlobClient(
        account_url=settings.STORAGE_ACCOUNT_URL,
        container_name=settings.STORAGE_CONTAINER_NAME,
        credential=settings.STORAGE_ACCESS_KEY,
        blob_name=filepath,
    ) as blob:
        try:
            await blob.upload_blob(data)
        except ResourceExistsError:
            return filepath
        except ResourceNotFoundError as error:
            logger.error(
                f"Could not upload file to Azure Storage Container: "
                f"{settings.STORAGE_ACCOUNT_URL}/{settings.STORAGE_CONTAINER_NAME}"
            )
            raise

    return filepath


async def invite_members_to_stream(email: str, stream_id: str, speckle_url: str):

    """Invites a member to be a part of the Speckle Stream"""

    client = get_speckle_client(speckle_url)
    client.stream.invite(
        stream_id=stream_id,
        email=email,
        message="You have been invited to a Speckle Stream as a collaborator!",
    )


async def remove_members_from_stream(stream_id: str, speckle_url: str):

    """Removes all members of a Speckle Stream"""

    client = get_speckle_client(speckle_url)
    stream = client.stream.get(id=stream_id)
    collaborators = stream.collaborators

    for collaborator in collaborators:
        client.stream.revoke_permission(stream_id=stream_id, user_id=collaborator.id)


def get_speckle_client(speckle_url: str) -> SpeckleClient:

    """Fetches the Speckle Client object"""

    client = SpeckleClient(speckle_url)
    client.authenticate_with_token(settings.SPECKLE_TOKEN)
    return client
