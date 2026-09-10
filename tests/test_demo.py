import json

from conveyor_dimensioning.demo import run_demo


def test_demo_creates_visualization_animation_scene_and_wms_json(tmp_path) -> None:
    result = run_demo(tmp_path, seed=42)

    assert result.status == "ok"
    for name in (
        "measurement.png",
        "conveyor_demo.gif",
        "example_measurement.json",
        "sample_scene.npz",
    ):
        assert (tmp_path / name).stat().st_size > 100
    payload = json.loads((tmp_path / "example_measurement.json").read_text())
    assert payload["measurement_status"] == "ok"
    assert payload["item_id"] == "synthetic-demo-001"
