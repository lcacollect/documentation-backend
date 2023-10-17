import json

from logic.export.to_lcax import get_life_cycle_stages


def test_get_life_cycle_stages(datafix_dir):
    project = json.loads((datafix_dir / "project_export.json").read_text())["data"]["projects"][0]

    stages = get_life_cycle_stages(project)

    assert stages == ["a1a3", "c3", "c4", "d"]
