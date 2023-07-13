from sqlalchemy.orm import selectinload
from sqlmodel import select

import models.reporting_schema as models_schema
import models.schema_category as models_category
import models.schema_element as models_element


async def query_for_lcax_export(reporting_schema_id: str, session) -> list[models_category.SchemaCategory]:
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
    schema_categories = await session.exec(query)
    return schema_categories.all()


def generate_lcax_schema(schema_categories: list[models_schema.SchemaCategory]) -> str:
    """Generate a CSV string of the database contents."""

    separator = ";"
    # Specify the fields
    format_ = separator.join(
        [
            "{class}",
            "{name}",
            "{source}",
            "{quantity}",
            "{unit}",
            "{description}",
        ]
    )
    # Generate the header row
    header = format_.replace("{", "").replace("}", "")
    row_list = [header]
    # Extract field values from SchemaElements
    for category in schema_categories:
        # ?: Create extra line for category here?
        for element in category.elements:
            values = {
                "class": element.schema_category.name,
                "name": element.name,
                "source": element.source.name if element.source else "Typed in",
                "quantity": element.quantity,
                "unit": element.unit,
                "description": element.description,
            }
            row_list.append(format_.format(**values))
    csv_str = "\n".join(row_list)
    return csv_str
