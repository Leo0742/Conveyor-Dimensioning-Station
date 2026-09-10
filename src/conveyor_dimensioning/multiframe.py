"""End-to-end moving-conveyor demonstration with robust window aggregation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from conveyor_dimensioning.measurement import aggregate_results, measure_scene
from conveyor_dimensioning.simulation import make_scene, sample_line_profiler_box, simulate_sequence
from conveyor_dimensioning.types import DimensionResult
from conveyor_dimensioning.visualization import plot_multiframe_summary, save_motion_gif
from conveyor_dimensioning.wms import WMSMessage


@dataclass(frozen=True)
class WindowRecord:
    frame_index: int
    encoder_mm: float
    zone_position_mm: float
    result: DimensionResult


@dataclass(frozen=True)
class MultiFrameEvidence:
    windows: tuple[WindowRecord, ...]
    aggregate: DimensionResult
    wms_message: WMSMessage


def run_multiframe_demo(output_dir: str | Path, *, seed: int = 42) -> MultiFrameEvidence:
    """Simulate entry, independent central windows, median aggregation and WMS JSON."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    positions = np.linspace(-400.0, 400.0, 9)
    records: list[WindowRecord] = []
    animation_points: np.ndarray | None = None
    for index, position in enumerate(positions):
        inside_zone = abs(position) <= 250.0
        if inside_zone:
            product = sample_line_profiler_box(
                (120.0, 80.0, 45.0),
                center_xy_mm=(35.0, float(position)),
                rotation_deg=(0.0, 0.0, 28.0),
                visible_completeness=0.88,
                edge_shadow=0.25,
                noise_std_mm=0.22,
                dropout=0.10,
                seed=seed + index * 10,
            ).points_mm
            animation_points = product - np.array([0.0, position, 0.0])
        else:
            product = np.empty((0, 3), dtype=float)
        scene = make_scene(product, plane_point_count=1600, seed=seed + index * 10 + 1)
        result = measure_scene(scene, seed=seed + index * 10 + 2)
        records.append(
            WindowRecord(
                frame_index=index,
                encoder_mm=float(index * 100.0),
                zone_position_mm=float(position),
                result=result,
            )
        )
    aggregate = aggregate_results([record.result for record in records])
    message = WMSMessage.from_result(
        "multiframe-demo-001",
        aggregate,
        timestamp=datetime(2026, 9, 9, 12, 30, tzinfo=UTC),
    )
    serialized = [
        {
            "frame_index": record.frame_index,
            "encoder_mm": record.encoder_mm,
            "zone_position_mm": record.zone_position_mm,
            "result": record.result.model_dump(),
        }
        for record in records
    ]
    (destination / "multiframe_windows.json").write_text(
        json.dumps(serialized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (destination / "multiframe_wms.json").write_text(
        message.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    plot_multiframe_summary(records, aggregate, destination / "multiframe_summary.png")
    if animation_points is None:
        raise RuntimeError("no central measurement window was generated")
    moving = animation_points + np.array([0.0, positions[0], 0.0])
    frames = simulate_sequence(moving, frame_count=9, fps=10.0, speed_mm_s=1000.0)
    save_motion_gif(frames, destination / "multiframe_motion.gif")
    return MultiFrameEvidence(tuple(records), aggregate, message)
