import csv

import numpy as np

from conveyor_dimensioning.benchmark import (
    measure_benchmark_case,
    regression_cases,
    run_benchmark,
    run_sensor_benchmark,
    with_hidden_reference,
)


def test_benchmark_writes_traceable_simulated_metrics(tmp_path) -> None:
    rows = run_benchmark(tmp_path, seed=100)

    assert len(rows) >= 6
    assert all("REGRESSION CASES" in row.evidence_type for row in rows)
    assert any(row.scenario == "small_10mm" for row in rows)
    assert any(row.scenario == "missing_points" for row in rows)
    assert (tmp_path / "benchmark.csv").exists()
    assert (tmp_path / "benchmark.md").exists()
    with (tmp_path / "benchmark.csv").open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    assert set(records[0]) >= {
        "scenario",
        "abs_error_length_mm",
        "relative_error_length_percent",
        "passed",
        "evidence_type",
    }
    assert all("REGRESSION CASES" in record["evidence_type"] for record in records)


def test_hidden_ground_truth_metadata_cannot_change_runtime_measurement() -> None:
    case = regression_cases(700)[1]
    changed = with_hidden_reference(case, (399.0, 299.0, 298.0))

    original_result = measure_benchmark_case(case, seed=88)
    changed_result = measure_benchmark_case(changed, seed=88)

    assert original_result == changed_result
    assert np.array_equal(case.points_mm, changed.points_mm)


def test_sensor_like_benchmark_is_separate_and_includes_irregular_shapes(tmp_path) -> None:
    rows = run_sensor_benchmark(tmp_path, seed=101)

    assert len(rows) >= 7
    assert all(
        row.evidence_type == "SIMPLIFIED LINE-PROFILER SYNTHETIC" for row in rows
    )
    assert {row.scenario for row in rows} >= {
        "sensor_l_prism",
        "sensor_cylinder",
        "sensor_composite",
    }
    assert (tmp_path / "sensor_benchmark_metrics.json").exists()
