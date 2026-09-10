"""Separated deterministic regression and sensor-like synthetic benchmarks."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np

from conveyor_dimensioning.config import MeasurementConfig
from conveyor_dimensioning.measurement import evaluate_result, measure_scene
from conveyor_dimensioning.simulation import (
    SENSOR_LIKE_EVIDENCE,
    make_scene,
    sample_box_surface,
    sample_line_profiler_shape,
)
from conveyor_dimensioning.types import DimensionResult

REGRESSION_EVIDENCE = "REGRESSION CASES (SIMULATED GEOMETRY)"
SENSOR_EVIDENCE = SENSOR_LIKE_EVIDENCE


@dataclass(frozen=True)
class BenchmarkCase:
    """Observed runtime input plus evaluator-only reference metadata."""

    scenario: str
    points_mm: np.ndarray
    reference_dimensions_mm: tuple[float, float, float]
    subset: str
    expected_reject: bool = False


@dataclass(frozen=True)
class BenchmarkRow:
    scenario: str
    subset: str
    ground_truth_length_mm: float
    ground_truth_width_mm: float
    ground_truth_height_mm: float
    measured_length_mm: float
    measured_width_mm: float
    measured_height_mm: float
    abs_error_length_mm: float
    abs_error_width_mm: float
    abs_error_height_mm: float
    relative_error_length_percent: float
    relative_error_width_percent: float
    relative_error_height_percent: float
    passed: bool
    expected_reject: bool
    false_ok: bool
    status: str
    evidence_type: str


def measure_benchmark_case(
    case: BenchmarkCase, *, config: MeasurementConfig | None = None, seed: int = 0
) -> DimensionResult:
    """Measure only observed points; evaluator-only metadata is intentionally unused."""
    return measure_scene(case.points_mm, config or MeasurementConfig(), seed=seed)


def with_hidden_reference(
    case: BenchmarkCase, reference_dimensions_mm: tuple[float, float, float]
) -> BenchmarkCase:
    """Replace evaluator metadata without changing runtime input."""
    return replace(case, reference_dimensions_mm=reference_dimensions_mm)


def _evaluate_case(
    case: BenchmarkCase, *, evidence_type: str, seed: int
) -> BenchmarkRow:
    result = measure_benchmark_case(case, seed=seed)
    evaluation = evaluate_result(result, case.reference_dimensions_mm)
    truth = np.sort(np.asarray(case.reference_dimensions_mm, dtype=float))[::-1]
    measured = np.array([result.length_mm, result.width_mm, result.height_mm])
    accepted = result.status == "ok"
    return BenchmarkRow(
        scenario=case.scenario,
        subset=case.subset,
        ground_truth_length_mm=float(truth[0]),
        ground_truth_width_mm=float(truth[1]),
        ground_truth_height_mm=float(truth[2]),
        measured_length_mm=float(measured[0]),
        measured_width_mm=float(measured[1]),
        measured_height_mm=float(measured[2]),
        abs_error_length_mm=float(evaluation.absolute_error_mm[0]),
        abs_error_width_mm=float(evaluation.absolute_error_mm[1]),
        abs_error_height_mm=float(evaluation.absolute_error_mm[2]),
        relative_error_length_percent=float(evaluation.relative_error_percent[0]),
        relative_error_width_percent=float(evaluation.relative_error_percent[1]),
        relative_error_height_percent=float(evaluation.relative_error_percent[2]),
        passed=evaluation.passed,
        expected_reject=case.expected_reject,
        false_ok=case.expected_reject and accepted,
        status=result.status,
        evidence_type=evidence_type,
    )


def regression_cases(seed: int) -> list[BenchmarkCase]:
    """Seven fixed geometry regression cases with dimension-independent density."""
    specifications = [
        ("axis_aligned", (120.0, 80.0, 40.0), (0.0, 0.0, 0.0), 0.0, 0.0),
        ("rotated_yaw", (120.0, 80.0, 40.0), (0.0, 0.0, 33.0), 0.0, 0.0),
        ("rotated_3d", (90.0, 55.0, 35.0), (8.0, 5.0, 21.0), 0.0, 0.0),
        ("small_10mm", (10.0, 10.0, 10.0), (0.0, 0.0, 17.0), 0.12, 0.08),
        ("large_limit", (400.0, 300.0, 300.0), (0.0, 0.0, 11.0), 0.25, 0.10),
        ("noisy", (160.0, 70.0, 35.0), (0.0, 0.0, 28.0), 0.45, 0.05),
        ("missing_points", (200.0, 100.0, 25.0), (0.0, 0.0, 41.0), 0.20, 0.40),
    ]
    cases = []
    for index, (name, dimensions, rotation, noise, dropout) in enumerate(specifications):
        product = sample_box_surface(
            dimensions,
            points_per_face=500,
            rotation_deg=rotation,
            noise_std_mm=noise,
            dropout=dropout,
            seed=seed + index * 10,
        )
        scene = make_scene(product, plane_point_count=1800, seed=seed + index * 10 + 1)
        cases.append(BenchmarkCase(name, scene, dimensions, "regression"))
    return cases


def sensor_cases(seed: int) -> list[BenchmarkCase]:
    """Fixed sensor-like cases covering boxes and reliable irregular references."""
    specifications = [
        ("sensor_box", "box", (120.0, 80.0, 40.0), (0.0, 0.0, 31.0)),
        ("sensor_small", "box", (10.0, 10.0, 10.0), (0.0, 0.0, 19.0)),
        ("sensor_l_prism", "l_prism", (100.0, 75.0, 35.0), (0.0, 0.0, 23.0)),
        ("sensor_cylinder", "cylinder", (80.0, 60.0, 30.0), (0.0, 0.0, 12.0)),
        ("sensor_composite", "composite", (110.0, 85.0, 45.0), (0.0, 0.0, 37.0)),
        ("sensor_tilt", "box", (90.0, 55.0, 35.0), (5.0, 4.0, 21.0)),
        ("sensor_incomplete", "box", (160.0, 70.0, 35.0), (0.0, 0.0, 28.0)),
    ]
    cases = []
    for index, (name, shape, dimensions, rotation) in enumerate(specifications):
        difficult = name == "sensor_incomplete"
        product = sample_line_profiler_shape(
            shape,
            dimensions,
            rotation_deg=rotation,
            visible_completeness=0.65 if difficult else 0.92,
            edge_shadow=0.45 if difficult else 0.20,
            noise_std_mm=0.40 if difficult else 0.15,
            dropout=0.25 if difficult else 0.05,
            seed=seed + index * 10,
        )
        scene = make_scene(product.points_mm, plane_point_count=1800, seed=seed + index * 10 + 1)
        cases.append(
            BenchmarkCase(name, scene, product.reference_dimensions_mm, "sensor-like")
        )
    return cases


def summarize_rows(rows: list[BenchmarkRow]) -> dict[str, object]:
    """Return per-axis percentiles and rejection metrics without hiding invalid rows."""
    valid = [row for row in rows if row.status == "ok" and not row.expected_reject]
    axis_names = ("length", "width", "height")
    absolute = np.array(
        [[getattr(row, f"abs_error_{axis}_mm") for axis in axis_names] for row in valid]
    )
    relative = np.array(
        [
            [getattr(row, f"relative_error_{axis}_percent") for axis in axis_names]
            for row in valid
        ]
    )

    def percentiles(values: np.ndarray) -> dict[str, dict[str, float | None]]:
        return {
            axis: {
                percentile: (float(np.percentile(values[:, index], level)) if len(values) else None)
                for percentile, level in (("p50", 50), ("p95", 95), ("p99", 99))
            }
            for index, axis in enumerate(axis_names)
        }

    expected_valid = [row for row in rows if not row.expected_reject]
    expected_reject_count = sum(row.expected_reject for row in rows)
    false_ok_count = sum(row.false_ok for row in rows)
    correct_ok_count = sum(row.passed for row in expected_valid)
    wrong_ok_count = sum(row.status == "ok" and not row.passed for row in expected_valid)
    rejected_expected_valid_count = sum(row.status != "ok" for row in expected_valid)
    accepted_count = correct_ok_count + wrong_ok_count
    return {
        "scenario_count": len(rows),
        "expected_valid_count": len(expected_valid),
        "correct_ok_count": correct_ok_count,
        "wrong_ok_count": wrong_ok_count,
        "rejected_expected_valid_count": rejected_expected_valid_count,
        "acceptance_rate": accepted_count / max(len(expected_valid), 1),
        "precision_among_accepted": correct_ok_count / max(accepted_count, 1),
        "correct_measurement_rate": correct_ok_count / max(len(expected_valid), 1),
        "invalid_rate": rejected_expected_valid_count / max(len(expected_valid), 1),
        "expected_reject_count": expected_reject_count,
        "correctly_rejected_expected_reject_count": expected_reject_count - false_ok_count,
        "false_ok_count": false_ok_count,
        "synthetic_rejection_stress_false_ok_rate": false_ok_count
        / max(expected_reject_count, 1),
        "absolute_error_mm": percentiles(absolute),
        "relative_error_percent": percentiles(relative),
    }


def _write_results(
    output_dir: str | Path,
    rows: list[BenchmarkRow],
    *,
    stem: str,
    heading: str,
) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / f"{stem}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(asdict(rows[0])), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    metrics = summarize_rows(rows)
    (destination / f"{stem}_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        f"# {heading}",
        "",
        "> Эти результаты проверяют программную геометрию на симулированных данных, "
        "а не абсолютную точность физической станции.",
        "",
        "| Сценарий | GT, мм | Измерено, мм | Статус | Допуск |",
        "|---|---:|---:|---|:---:|",
    ]
    for row in rows:
        truth = (
            f"{row.ground_truth_length_mm:.1f}×{row.ground_truth_width_mm:.1f}×"
            f"{row.ground_truth_height_mm:.1f}"
        )
        measured = (
            f"{row.measured_length_mm:.2f}×{row.measured_width_mm:.2f}×"
            f"{row.measured_height_mm:.2f}"
        )
        lines.append(
            f"| {row.scenario} | {truth} | {measured} | {row.status} | "
            f"{'да' if row.passed else 'нет'} |"
        )
    lines.extend(
        [
            "",
            f"Correct measurement rate: {metrics['correct_measurement_rate']:.1%}",
            f"Evidence: {heading}",
            "",
        ]
    )
    (destination / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8")


def run_regression_benchmark(output_dir: str | Path, *, seed: int = 42) -> list[BenchmarkRow]:
    rows = [
        _evaluate_case(case, evidence_type=REGRESSION_EVIDENCE, seed=seed + index)
        for index, case in enumerate(regression_cases(seed))
    ]
    _write_results(output_dir, rows, stem="regression_benchmark", heading=REGRESSION_EVIDENCE)
    return rows


def run_sensor_benchmark(output_dir: str | Path, *, seed: int = 42) -> list[BenchmarkRow]:
    rows = [
        _evaluate_case(case, evidence_type=SENSOR_EVIDENCE, seed=seed + index)
        for index, case in enumerate(sensor_cases(seed))
    ]
    _write_results(output_dir, rows, stem="sensor_benchmark", heading=SENSOR_EVIDENCE)
    return rows


def run_benchmark(output_dir: str | Path, *, seed: int = 42) -> list[BenchmarkRow]:
    """Compatibility entry point for the seven regression cases."""
    rows = run_regression_benchmark(output_dir, seed=seed)
    destination = Path(output_dir)
    for suffix in ("csv", "md"):
        source = destination / f"regression_benchmark.{suffix}"
        (destination / f"benchmark.{suffix}").write_bytes(source.read_bytes())
    return rows
