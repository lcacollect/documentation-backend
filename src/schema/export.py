import base64
import json
from enum import Enum

import strawberry
from lcacollect_config.context import get_session, get_token
from strawberry.types import Info

from logic.export.to_csv import generate_csv_schema, query_for_csv_export
from logic.export.to_lcabyg import aggregate_lcabyg_models, query_for_lca_byg_export
from logic.export.to_lcax import generate_lcax_schema, query_for_lcax_export


@strawberry.enum(name="exportFormat")
class ExportFormat(Enum):
    """Available export formats."""

    LCABYG = "lcayg"
    CSV = "csv"
    LCAX = "lcax"


async def export_reporting_schema_mutation(info: Info, reporting_schema_id: str, export_format: ExportFormat) -> str:
    """Resolver for exporting the database contents as a base64 encoded string."""

    session = get_session(info)
    token = get_token(info)

    if export_format is ExportFormat.LCABYG:
        schema_categories, assemblies = await query_for_lca_byg_export(reporting_schema_id, session, token)
        entity_list = aggregate_lcabyg_models(schema_categories, assemblies)
        data = json.dumps([entity.as_dict() for entity in entity_list], indent=4)

    elif export_format is ExportFormat.CSV:
        schema_categories = await query_for_csv_export(reporting_schema_id, session)
        data = generate_csv_schema(schema_categories)

    elif export_format is ExportFormat.LCAX:
        project, reporting_schema, schema_categories, assemblies = await query_for_lcax_export(
            reporting_schema_id, session, token
        )
        data = generate_lcax_schema(project, reporting_schema, schema_categories, assemblies)

    else:
        raise NotImplementedError

    return str(base64.b64encode(data.encode("utf-8")), "utf-8")
