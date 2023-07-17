import json

from logic.export.to_lcax import get_life_cycle_stages


def test_get_life_cycle_stages(datafix_dir):
    project = json.loads((datafix_dir / "project_export.json").read_text())["data"]["projects"][0]

    stages = get_life_cycle_stages(project)

    assert stages == ["A1A3", "C3", "C4", "D"]
