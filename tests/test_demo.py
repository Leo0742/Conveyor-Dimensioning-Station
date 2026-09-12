import json
from pathlib import Path

import numpy as np

import conveyor_dimensioning.demo as demo_module
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


def test_demo_visualization_uses_reported_dimensions(tmp_path, monkeypatch) -> None:
    captured: dict[str, np.ndarray | None] = {"dimensions": None}

    def capture_plot(
        scene_points_mm,
        object_points_mm,
        box,
        output_path,
        *,
        reported_dimensions_mm=None,
    ) -> None:
        captured["dimensions"] = reported_dimensions_mm
        Path(output_path).write_bytes(b"x" * 101)

    monkeypatch.setattr(demo_module, "plot_measurement", capture_plot)
    monkeypatch.setattr(
        demo_module,
        "save_motion_gif",
        lambda frames, output_path: Path(output_path).write_bytes(b"x" * 101),
    )

    result = run_demo(tmp_path, seed=42)

    np.testing.assert_allclose(
        captured["dimensions"],
        [result.length_mm, result.width_mm, result.height_mm],
    )
