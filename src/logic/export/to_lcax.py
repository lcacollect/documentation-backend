import importlib.metadata
from datetime import datetime

from lcax import (
    EPD,
    Assembly,
    Classification,
    Conversion,
    EPDPart,
    EPDSourceItem,
    ImpactCategoryKey,
    LCAxProject,
    LifeCycleStage,
    Source,
    Standard,
    Unit,
)
from sqlalchemy.orm import selectinload
from sqlmodel import select

import models.reporting_schema as models_schema
import models.reporting_schema as models_reporting
import models.schema_category as models_category
import models.schema_element as models_element
from logic.export.utils import query_assemblies_for_export, query_project_for_export


async def query_for_lcax_export(
    reporting_schema_id: str, session, token: str
) -> tuple[dict | None, models_reporting.ReportingSchema, list[models_category.SchemaCategory], list[dict] | None]:
    """Query the database for SchemaCategories and the required attributes for CSV export."""

    query = (
        select(models_schema.SchemaCategory)
        .where(models_category.SchemaCategory.reporting_schema_id == reporting_schema_id)
        .options(selectinload(models_schema.SchemaCategory.reporting_schema))
        .options(
            selectinload(models_category.SchemaCategory.elements)
            .options(selectinload(models_element.SchemaElement.schema_category))
            .options(selectinload(models_element.SchemaElement.source))
        )
    )
    schema_categories = (await session.exec(query)).all()
    reporting_schema = schema_categories[0].reporting_schema
    project = await query_project_for_export(reporting_schema.project_id, token)
    assemblies = await query_assemblies_for_export(reporting_schema.project_id, token)

    return project, reporting_schema, schema_categories, assemblies


def generate_lcax_schema(
    project: dict,
    reporting_schema: models_reporting.ReportingSchema,
    schema_categories: list[models_schema.SchemaCategory],
    assemblies: list[dict],
) -> str:
    """Generate a LCAx string of the database contents."""

    classification_system = get_classification_system(reporting_schema)

    lcax_project = LCAxProject(
        id=project["id"],
        name=project["name"],
        description="LCAcollect Project",
        comment=f"Exported ${datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        classification_system=classification_system,
        emission_parts=get_assemblies(schema_categories, classification_system, assemblies, project),
        format_version=importlib.metadata.version("lcax"),
        impact_categories=[ImpactCategoryKey.gwp],
        lcia_method="EN15978",
        life_cycle_stages=get_life_cycle_stages(project),
        life_span=50,
        location=project["country"] or "DK",
    )

    return lcax_project.json(by_alias=True)


def get_life_cycle_stages(project: dict) -> list[LifeCycleStage]:
    stages = []
    for stage in project.get("stages"):
        if stage.get("phase") == "A1-A3":
            stages.append("a1a3")
        else:
            stages.append(stage.get("phase", "").lower())
    return stages


def get_assemblies(
    schema_categories: list[models_schema.SchemaCategory],
    classification_system: str | None,
    graphql_assemblies: list[dict],
    project: dict,
) -> dict[str, Assembly]:
    assemblies = {}

    for category in schema_categories:
        for element in category.elements:
            assembly = Assembly(
                classification=[
                    Classification(
                        system=classification_system,
                        code=element.schema_category.name.split(" | ")[0],
                        name=element.schema_category.name.split(" | ")[1],
                    )
                ]
                if classification_system
                else None,
                description=element.description,
                id=element.id,
                name=element.name,
                parts=get_parts(element, graphql_assemblies, project),
                quantity=element.quantity,
                unit=convert_to_lcax_unit(element.unit),
            )
            assemblies[assembly.id] = assembly

    return assemblies


class EPDPartTransportation(EPDPart):
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

    transport_type: str | None
    transport_distance: str | None
    transport_unit = str | None


def get_parts(
    element: models_element.SchemaElement, graphql_assemblies: list[dict], project: dict
) -> dict[str, EPDPart]:
    epd_parts = {}

    for assembly in graphql_assemblies:
        if assembly.get("id") == element.assembly_id:
            for layer in assembly.get("layers"):
                epd_source = EPD(
                    id=layer.get("epd", {}).get("id"),
                    name=layer.get("epd", {}).get("name"),
                    location=layer.get("epd", {}).get("location"),
                    published_date=datetime.strptime(layer.get("epd", {}).get("publishedDate"), "%Y-%m-%d"),
                    valid_until=datetime.strptime(layer.get("epd", {}).get("validUntil"), "%Y-%m-%d"),
                    declared_unit=convert_to_lcax_unit(layer.get("epd", {}).get("declaredUnit")),
                    format_version=importlib.metadata.version("lcax"),
                    version=layer.get("epd", {}).get("version"),
                    source=Source(name=layer.get("epd", {}).get("source")),
                    subtype=layer.get("epd", {}).get("subtype"),
                    standard=Standard.en15804_a1,
                    reference_service_life=layer.get("epd", {}).get("referenceServiceLife"),
                    comment=layer.get("epd", {}).get("comment"),
                    conversions=[
                        Conversion(to=convert_to_lcax_unit(conversion.get("to")), value=conversion.get("value"))
                        for conversion in layer.get("epd", {}).get("conversions")
                    ],
                    gwp=layer.get("epd", {}).get("gwp"),
                )
                if hasTrasportPhase(project):
                    epd_part = EPDPartTransportation(
                        id=layer.get("id"),
                        name=layer.get("name"),
                        part_quantity=layer.get("conversionFactor"),
                        part_unit=convert_to_lcax_unit(layer.get("unit")),
                        reference_service_life=layer.get("referenceServiceLife"),
                        epd_source=EPDSourceItem(epd=epd_source),
                        transport_type=layer.get("transportType"),
                        transport_distance=layer.get("transportDistance"),
                        transport_unit=layer.get("transportUnit"),
                    )
                else:
                    epd_part = EPDPart(
                        id=layer.get("id"),
                        name=layer.get("name"),
                        part_quantity=layer.get("conversionFactor"),
                        part_unit=convert_to_lcax_unit(layer.get("unit")),
                        reference_service_life=layer.get("referenceServiceLife"),
                        epd_source=EPDSourceItem(epd=epd_source),
                    )
                epd_parts[epd_part.id] = epd_part

    return epd_parts


def hasTrasportPhase(project: dict):
    trasportPhase = False
    for stage in project.get("stages"):
        if stage.get("phase").lower() == "a4":
            trasportPhase = True
    return trasportPhase


def convert_to_lcax_unit(unit: str) -> Unit:
    match unit:
        case "pcs":
            return Unit.pcs
        case "m":
            return Unit.m
        case "m2":
            return Unit.m2
        case "m3":
            return Unit.m3
        case "kg":
            return Unit.kg
        case "l":
            return Unit.l
        case _:
            return Unit.unknown


def get_classification_system(reporting_schema: models_reporting.ReportingSchema) -> str | None:
    if reporting_schema.name == "BR23 - BIMTypeCode":
        return "BIMTypeCode"
    else:
        return None
