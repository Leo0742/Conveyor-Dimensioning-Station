"""Generate submission-ready artifacts from a deterministic synthetic scene."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from conveyor_dimensioning.config import MeasurementConfig
from conveyor_dimensioning.geometry import dominant_top_plane_box
from conveyor_dimensioning.measurement import estimate_support_contact_completion, measure_scene
from conveyor_dimensioning.preprocessing import (
    fit_conveyor_plane_ransac,
    remove_plane,
    statistical_filter,
)
from conveyor_dimensioning.simulation import make_scene, sample_line_profiler_box, simulate_sequence
from conveyor_dimensioning.types import DimensionResult
from conveyor_dimensioning.visualization import plot_measurement, save_motion_gif
from conveyor_dimensioning.wms import WMSMessage


def run_demo(output_dir: str | Path, *, seed: int = 42) -> DimensionResult:
    """Build the example scene, run the pipeline and save visual/WMS outputs."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    simulated = sample_line_profiler_box(
        (120.0, 80.0, 45.0),
        rotation_deg=(0.0, 0.0, 28.0),
        noise_std_mm=0.22,
        dropout=0.08,
        seed=seed,
    )
    product = simulated.points_mm
    scene = make_scene(
        product,
        plane_point_count=2400,
        plane_noise_std_mm=0.12,
        seed=seed + 1,
    )
    config = MeasurementConfig()
    measurement_seed = seed + 2
    result = measure_scene(scene, config, seed=measurement_seed)

    # Rebuild the same observed object used by measure_scene only for visualization.
    plane, _ = fit_conveyor_plane_ransac(
        scene,
        threshold_mm=config.plane_distance_threshold_mm,
        iterations=config.ransac_iterations,
        seed=measurement_seed,
    )
    isolated = remove_plane(
        scene,
        plane,
        min_height_mm=config.object_min_height_mm,
    )
    isolated = statistical_filter(
        isolated,
        neighbors=config.outlier_neighbors,
        std_ratio=config.outlier_std_ratio,
    )
    augmented = estimate_support_contact_completion(isolated, plane)
    box = dominant_top_plane_box(augmented, seed=measurement_seed)

    np.savez_compressed(destination / "sample_scene.npz", points_mm=scene)
    plot_measurement(scene, isolated, box, destination / "measurement.png")

    moving_product = product + np.array([0.0, -300.0, 0.0])
    frames = simulate_sequence(
        moving_product,
        frame_count=12,
        fps=20.0,
        speed_mm_s=1000.0,
    )
    save_motion_gif(frames, destination / "conveyor_demo.gif")

    message = WMSMessage.from_result(
        "synthetic-demo-001",
        result,
        timestamp=datetime(2026, 9, 9, 12, 0, tzinfo=UTC),
    )
    (destination / "example_measurement.json").write_text(
        message.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    run_demo(Path("assets/demo"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
