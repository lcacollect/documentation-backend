import datetime
import logging
from io import StringIO
from typing import Optional

import numpy as np
import pandas
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobClient
from lcacollect_config.formatting import string_uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, Relationship, SQLModel

from core.config import settings
from models.schema_element import SchemaElement

logger = logging.getLogger(__name__)


class ProjectSource(SQLModel, table=True):
    """ProjectSource database class"""

    id: Optional[str] = Field(default_factory=string_uuid, primary_key=True, index=True)
    type: str
    data_id: str
    name: str
    project_id: str
    meta_fields: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    elements: list[SchemaElement] = Relationship(back_populates="source")
    interpretation: dict = Field(default=dict, sa_column=Column(JSON), nullable=False)
    author_id: str | None
    updated: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.now, nullable=False)

    @property
    def data(self):
        from schema.source import ProjectSourceType

        if self.type in (ProjectSourceType.CSV.value, ProjectSourceType.XLSX.value):
            with BlobClient(
                account_url=settings.STORAGE_ACCOUNT_URL,
                container_name=settings.STORAGE_CONTAINER_NAME,
                credential=settings.STORAGE_ACCESS_KEY,
                blob_name=self.data_id,
            ) as blob:
                try:
                    stream = blob.download_blob()
                    raw_data = stream.readall()

                    # reader: [{"col1_name": "row_val", "col2_name":..}, {...}]
                    if self.type == ProjectSourceType.CSV.value:
                        data = raw_data.decode()
                        header = data[: data.index("\n")]
                        if header.count(";") >= 2:
                            sep = ";"
                            dec = ","
                        else:
                            sep = ","
                            dec = "."
                        file_data = StringIO(data)
                        reader = (
                            pandas.read_csv(file_data, sep=sep, decimal=dec).replace({np.nan: None}).to_dict("records")
                        )

                    elif self.type == ProjectSourceType.XLSX.value:
                        reader = pandas.read_excel(raw_data).replace({np.nan: None}).to_dict("records")

                    rows = [{**row, "id": index} for index, row in enumerate(reader)]
                    return list(rows[0].keys()), rows
                except ResourceNotFoundError:
                    logger.error(
                        f"Could not download file from Azure Storage Container: "
                        f"{settings.STORAGE_ACCOUNT_URL}/{settings.STORAGE_CONTAINER_NAME}"
                    )
                    return [], []

        else:
            raise NotImplementedError(f"Only ProjectSourceType CSV or XLSX is allowed")
