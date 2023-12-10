import pytest

from unittest.mock import PropertyMock
from models.schema_category import SchemaCategory
from models.schema_element import SchemaElement
from logic.export.to_csv import generate_csv_schema


@pytest.mark.asyncio
async def test_csv_element(category: SchemaCategory, mocker):
    """Test that SchemaElement is correctly written to CSV."""

    m = mocker.patch("models.schema_element.SchemaElement.source", new_callable=PropertyMock)
    m.return_value = False

    expected_csv = """\
"class";"name";"source";"quantity";"unit";"description"
"211 | Udvendige vægelementer";"Wall";"Typed in";2500.0;"m3";"A 5th century oak palisade wall."
""".replace(
        "\r\n", "\n"
    )

    generated_csv = generate_csv_schema([category]).replace("\r\n", "\n")

    assert expected_csv == generated_csv
