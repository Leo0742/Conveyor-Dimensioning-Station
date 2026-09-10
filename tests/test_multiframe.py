import json

import numpy as np

from conveyor_dimensioning.multiframe import run_multiframe_demo


def test_multiframe_demo_aggregates_valid_windows_and_writes_wms(tmp_path) -> None:
    evidence = run_multiframe_demo(tmp_path, seed=303)
    valid = [record.result for record in evidence.windows if record.result.status == "ok"]
    dimensions = np.array(
        [[result.length_mm, result.width_mm, result.height_mm] for result in valid]
    )

    assert len(evidence.windows) >= 7
    assert len(valid) >= 3
    assert np.allclose(
        [
            evidence.aggregate.length_mm,
            evidence.aggregate.width_mm,
            evidence.aggregate.height_mm,
        ],
        np.median(dimensions, axis=0),
    )
    payload = json.loads((tmp_path / "multiframe_wms.json").read_text())
    assert payload["length_mm"] == evidence.aggregate.length_mm
    assert payload["width_mm"] == evidence.aggregate.width_mm
    assert payload["height_mm"] == evidence.aggregate.height_mm
    assert payload["measurement_status"] == "ok"
    assert (tmp_path / "multiframe_windows.json").exists()
    assert (tmp_path / "multiframe_summary.png").exists()
    assert (tmp_path / "multiframe_motion.gif").exists()
