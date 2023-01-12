import csv
import logging
from typing import Optional

import strawberry
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobClient, ContainerClient
from strawberry.scalars import JSON
from strawberry.types import Info

from core.config import settings
from schema.source import ProjectSourceType

logger = logging.getLogger(__name__)


@strawberry.type
class GraphQLProjectSourceFile:
    data_id: str
    headers: JSON
    rows: JSON


async def project_source_files_query(
    info: Info,
    data_ids: Optional[list[str]] | None = None,
    type: ProjectSourceType | None = ProjectSourceType.CSV,
) -> list[GraphQLProjectSourceFile]:
    """Get source files with a list of data ids"""

    if type is not ProjectSourceType.CSV:
        raise NotImplementedError(f"Only ProjectSourceType CSV is allowed")

    source_files = []

    if data_ids is None:
        container = ContainerClient(
            account_url=settings.STORAGE_ACCOUNT_URL,
            container_name=settings.STORAGE_CONTAINER_NAME,
            credential=settings.STORAGE_ACCESS_KEY,
        )
        blobs = container.list_blobs(name_starts_with=f"{settings.STORAGE_BASE_PATH}")
        for blob in blobs:
            data_id = blob.name
            if data_id is not None and data_id != "":
                source_file = construct_source_file(data_id)
                source_files.append(source_file)

    else:
        for data_id in data_ids:
            if data_id is not None and data_id != "":
                source_file = construct_source_file(data_id)
                source_files.append(source_file)

    return source_files


async def construct_source_file(data_id: str):
    TMP_FILE = f"{data_id[11:]}.csv"
    with BlobClient(
        account_url=settings.STORAGE_ACCOUNT_URL,
        container_name=settings.STORAGE_CONTAINER_NAME,
        credential=settings.STORAGE_ACCESS_KEY,
        blob_name=data_id,
    ) as blob:
        try:
            with open(TMP_FILE, "wb") as my_blob:
                stream = blob.download_blob()
                data = stream.readall()
                my_blob.write(data)
            with open(TMP_FILE, newline="") as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                line_count = 0
                rows = []
                for row in reader:
                    if line_count == 0:
                        headers = row
                        line_count += 1
                    else:
                        rowObj = dict(zip(headers, row))
                        rowObj["id"] = line_count - 1
                        rows.append(rowObj)
                        line_count += 1
        except ResourceNotFoundError as error:
            logger.error(
                f"Could not download file from Azure Storage Container: "
                f"{settings.STORAGE_ACCOUNT_URL}/{settings.STORAGE_CONTAINER_NAME}"
            )
            raise

    source_file = GraphQLProjectSourceFile(data_id=data_id, headers=headers, rows=rows)
    return source_file
