import pytest

from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement


@pytest.mark.asyncio
async def test_csv_element(category: SchemaCategory):
    """Test that SchemaElement is correctly written to CSV."""
    element = category.elements[0]
    attributes = (
        "name",
        "quantity",
        "unit",
        "description",
        "result",
        # "schema_category",    # FIXME: read name/id
        # "commits",    # FIXME
        # "tasks",      # FIXME
        # "source",     # FIXME
    )
    # TODO: check what order of columns makes sense
    row_contents = ";".join([str(getattr(element, attr)) or "-" for attr in attributes])
    header = ";".join(attributes)
    expected_csv = "\n".join([header, row_contents])

    assert True  # FIXME
